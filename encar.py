import requests
from datetime import datetime
from tqdm import tqdm
from urllib.parse import quote


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

fileName = input('차량 검색 조건 입력 (파일명): ')
full_url = input('API URL 전체 입력: ').strip()
while not full_url:
    full_url = input().strip()
f = open(datetime.now().strftime("%Y-%m-%d_%H_%M_%S") + '_' + fileName +'.md', 'w')


# sr 파라미터에서 offset/count 부분만 교체
# sr=%7CModifiedDate%7C{offset}%7C{count} 형태
sr_idx = full_url.find('sr=')
if sr_idx == -1:
    print('URL에서 sr 파라미터를 찾을 수 없습니다.')
    exit(1)

sr_part = full_url[sr_idx:]
amp_idx = sr_part.find('&')
if amp_idx != -1:
    sr_part = sr_part[:amp_idx]

# sr=%7CModifiedDate%7C0%7C8 에서 마지막 두 %7C 구간을 교체
parts = sr_part.split('%7C')  # ['sr=', 'ModifiedDate', '0', '8']
sr_base = '%7C'.join(parts[:-2])  # 'sr=%7CModifiedDate'


def build_url(offset, count=50):
    new_sr = f'{sr_base}%7C{offset}%7C{count}'
    return full_url[:sr_idx] + new_sr + full_url[sr_idx + len(sr_part):]


response = requests.get(build_url(0))
data = response.json()
count = int(data['Count'])

print(f'총 {count}개의 차량을 검색합니다.')

carList = []
for num in range(0, count + 1, 50):
    response = requests.get(build_url(num))
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

message = '총 ' + str(count) + '개의 결과에서 영업용도 사용 이력이 없고 명의 변경 횟수가 2회 이하인 차는 다음과 같습니다.\n\n'
f.write(message)
f.write("|번호|명의 변경|가격|사고 횟수|평균 피해액|마일리지|URL|\n|---|---|---|---|---|---|---|\n")
ret.sort(key=lambda x: x[2])
for idx, (_, num_changed, cost, accident_cnt, avg_cost, mileage, target_url) in enumerate(ret, 1):
    f.write(f'|{idx}|{num_changed}|{cost}만원|{accident_cnt}회|{avg_cost}만원|{mileage}km|[URL]({target_url})|\n')

f.close()

print('파일 생성이 완료되었습니다.')
