import html
import json
import os
import requests
from datetime import datetime
from tqdm import tqdm
from urllib.parse import quote, unquote


def parse_page_url(page_url):
    """엔카 페이지 URL에서 검색 쿼리와 정렬 기준을 추출"""
    fragment_idx = page_url.find('#!')
    if fragment_idx == -1:
        print('URL에서 검색 조건을 찾을 수 없습니다. 엔카 검색 결과 페이지 URL을 입력해주세요.')
        exit(1)
    fragment = unquote(page_url[fragment_idx + 2:])
    params = json.loads(fragment)
    query = params.get('action', '')
    sort = params.get('sort', 'ModifiedDate')
    return query, sort


def build_api_url(query, sort, offset, count=50):
    """API URL 생성"""
    encoded_query = quote(query, safe='()._')
    return (
        f'https://api.encar.com/search/car/list/general'
        f'?count=true'
        f'&q={encoded_query}'
        f'&sr=%7C{sort}%7C{offset}%7C{count}'
        f'&inav=%7CMetadata%7CSort'
    )


def getVehicleInfo(car_id):
    """차량 기본 정보 (vehicleNo 포함) 조회"""
    url = f'https://api.encar.com/v1/readside/vehicle/{car_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def getRecordInfo(car_id, vehicle_no):
    """보험 이력 정보 조회 (용도 이력, 명의 변경, 사고 이력 등)"""
    encoded_no = quote(vehicle_no)
    url = f'https://api.encar.com/v1/readside/record/vehicle/{car_id}/open?vehicleNo={encoded_no}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def isRentCar(record_info):
    """렌트카/영업용 여부 확인"""
    if not record_info:
        return False
    # government: 관용, business: 영업용, loan: 대여
    return record_info.get('government', 0) > 0 or \
           record_info.get('business', 0) > 0 or \
           record_info.get('loan', 0) > 0


def getOwnerChangeCnt(record_info):
    """명의 변경 횟수"""
    if not record_info:
        return 999
    return record_info.get('ownerChangeCnt', 999)


def getAccidentInfo(record_info):
    """사고 정보 (횟수, 총 피해액)"""
    if not record_info:
        return 0, 0
    accident_cnt = record_info.get('myAccidentCnt', 0)
    accident_cost = record_info.get('myAccidentCost', 0)
    return accident_cnt, accident_cost


def getTargetUrl(car_id, position=1):
    base_url = f'https://fem.encar.com/cars/detail/{car_id}'
    params = f'?pageid=fc_carsearch&listAdvType=normal&carid={car_id}&view_type=hs_ad&adv_attribute=hs_ad&wtClick_forList=019&advClickPosition=imp_normal_p1_g{position}'
    return base_url + params


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { color-scheme: light dark; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
    margin: 0; padding: 32px 20px; background: #fafafa; color: #1a1a1a;
  }
  h1 { font-size: 20px; margin: 0 0 6px; }
  .summary { font-size: 14px; color: #666; margin-bottom: 20px; }
  .hint { font-size: 13px; color: #888; margin-bottom: 12px; }
  .table-wrap { overflow-x: auto; background: #fff; border: 1px solid #e2e2e2; border-radius: 8px; }
  table { border-collapse: collapse; width: 100%; font-size: 14px; }
  th, td { padding: 10px 14px; text-align: right; white-space: nowrap; border-bottom: 1px solid #eee; }
  th:first-child, td:first-child, th:last-child, td:last-child { text-align: center; }
  thead th {
    position: sticky; top: 0; background: #f4f4f5; font-weight: 600;
    border-bottom: 1px solid #ddd; user-select: none;
  }
  thead th[data-type] { cursor: pointer; }
  thead th[data-type]:hover { background: #e9e9eb; }
  thead th[data-type]::after { content: " ↕"; color: #bbb; }
  thead th[data-order="asc"]::after { content: " ↑"; color: #1a1a1a; }
  thead th[data-order="desc"]::after { content: " ↓"; color: #1a1a1a; }
  tbody tr:hover { background: #f8f8fb; }
  tbody tr:last-child td { border-bottom: none; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }
  @media (prefers-color-scheme: dark) {
    body { background: #17171a; color: #e6e6e6; }
    .summary, .hint { color: #9a9a9a; }
    .table-wrap { background: #1f1f23; border-color: #33333a; }
    th, td { border-bottom-color: #2b2b31; }
    thead th { background: #26262b; border-bottom-color: #38383f; }
    thead th[data-type]:hover { background: #2f2f36; }
    thead th[data-order="asc"]::after, thead th[data-order="desc"]::after { color: #e6e6e6; }
    tbody tr:hover { background: #26262b; }
    a { color: #7aa7ff; }
  }
</style>
</head>
<body>
<h1>__TITLE__</h1>
<p class="summary">__SUMMARY__</p>
<p class="hint">열 제목을 클릭하면 해당 항목으로 정렬됩니다. (다시 클릭하면 오름차순/내림차순 전환)</p>
<div class="table-wrap">
<table>
<thead>
<tr>
  <th data-type="number" data-order="asc">번호</th>
  <th data-type="number">명의 변경</th>
  <th data-type="number">가격</th>
  <th data-type="number">사고 횟수</th>
  <th data-type="number">평균 피해액</th>
  <th data-type="number">마일리지</th>
  <th>링크</th>
</tr>
</thead>
<tbody>
__ROWS__
</tbody>
</table>
</div>
<script>
(function () {
  var table = document.querySelector('table');
  var tbody = table.tBodies[0];
  var headers = table.querySelectorAll('thead th');

  headers.forEach(function (th, idx) {
    if (!th.dataset.type) return;
    th.addEventListener('click', function () {
      var asc = th.dataset.order !== 'asc';
      headers.forEach(function (other) { delete other.dataset.order; });
      th.dataset.order = asc ? 'asc' : 'desc';

      var dir = asc ? 1 : -1;
      var rows = Array.prototype.slice.call(tbody.rows);
      rows.sort(function (a, b) {
        var av = a.cells[idx].dataset.value;
        var bv = b.cells[idx].dataset.value;
        if (th.dataset.type === 'number') return (Number(av) - Number(bv)) * dir;
        return String(av).localeCompare(String(bv), 'ko') * dir;
      });
      rows.forEach(function (row) { tbody.appendChild(row); });
    });
  });
})();
</script>
</body>
</html>
'''


def build_html(title, summary, rows):
    """정렬 가능한 HTML 테이블 문서 생성"""
    row_html = []
    for rank, num_changed, cost, accident_cnt, avg_cost, mileage, target_url in rows:
        row_html.append(
            '<tr>'
            f'<td data-value="{rank}">{rank}</td>'
            f'<td data-value="{num_changed}">{num_changed}회</td>'
            f'<td data-value="{cost}">{cost:,}만원</td>'
            f'<td data-value="{accident_cnt}">{accident_cnt}회</td>'
            f'<td data-value="{avg_cost}">{avg_cost:,}만원</td>'
            f'<td data-value="{mileage}">{mileage:,}km</td>'
            f'<td data-value="{rank}"><a href="{html.escape(target_url, quote=True)}" target="_blank" rel="noopener">보기</a></td>'
            '</tr>'
        )
    return (HTML_TEMPLATE
            .replace('__TITLE__', html.escape(title))
            .replace('__SUMMARY__', html.escape(summary))
            .replace('__ROWS__', '\n'.join(row_html)))


fileName = input('차량 검색 조건 입력 (파일명): ')
page_url = input('엔카 검색 결과 페이지 URL 입력: ').strip()
while not page_url:
    page_url = input().strip()
query, sort = parse_page_url(page_url)
RESULT_DIR = 'result'
os.makedirs(RESULT_DIR, exist_ok=True)
outputPath = os.path.join(
    RESULT_DIR,
    datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + '_' + fileName + '.html',
)


response = requests.get(build_api_url(query, sort, 0))
data = response.json()
count = int(data['Count'])

print(f'총 {count}개의 차량을 검색합니다.')

carList = []
for num in range(0, count + 1, 50):
    response = requests.get(build_api_url(query, sort, num))
    data = response.json()
    for carData in data['SearchResults']:
        carList.append((carData['Id'], int(carData['Price']), int(carData['Mileage'])))

cnt = 0
ret = []
for i in tqdm(range(len(carList))):
    car = carList[i]
    car_id = car[0]
    cost = car[1]
    mileage = car[2]

    # 차량 기본 정보 조회 (vehicleNo 획득)
    vehicle_info = getVehicleInfo(car_id)
    if not vehicle_info:
        continue

    vehicle_no = vehicle_info.get('vehicleNo')
    if not vehicle_no:
        continue

    # 보험 이력 정보 조회
    record_info = getRecordInfo(car_id, vehicle_no)

    # 렌트카/영업용 여부 확인
    if isRentCar(record_info):
        continue

    # 명의 변경 횟수 확인
    num_changed = getOwnerChangeCnt(record_info)
    if num_changed > 2:
        continue

    # 사고 정보
    accident_cnt, accident_cost = getAccidentInfo(record_info)
    avg_accident_cost = accident_cost // accident_cnt // 10000 if accident_cnt > 0 else 0

    cnt += 1
    target_url = getTargetUrl(car_id, cnt)
    ret.append((cnt, num_changed, cost, accident_cnt, avg_accident_cost, mileage, target_url))

summary = f'총 {count}개의 결과에서 영업용도 사용 이력이 없고 명의 변경 횟수가 2회 이하인 차 {len(ret)}대입니다.'
ret.sort(key=lambda x: x[2])
rows = [
    (idx, num_changed, cost, accident_cnt, avg_cost, mileage, target_url)
    for idx, (_, num_changed, cost, accident_cnt, avg_cost, mileage, target_url) in enumerate(ret, 1)
]

with open(outputPath, 'w', encoding='utf-8') as f:
    f.write(build_html(fileName, summary, rows))

print(f'파일 생성이 완료되었습니다. ({outputPath})')
