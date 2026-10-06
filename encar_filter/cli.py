"""CLI 입출력과 실행 흐름."""
import os
from datetime import datetime

from tqdm import tqdm

from .api import EncarApi
from .collector import CarCollector
from .filters import CarFilter
from .report import render_report
from .urls import InvalidPageUrlError, parse_page_url

RESULT_DIR = 'result'


def main():
    file_name = input('차량 검색 조건 입력 (파일명): ')
    page_url = input('엔카 검색 결과 페이지 URL 입력: ').strip()
    while not page_url:
        page_url = input().strip()

    try:
        query, sort = parse_page_url(page_url)
    except InvalidPageUrlError as error:
        print(error)
        raise SystemExit(1)

    car_filter = CarFilter()
    collector = CarCollector(EncarApi(), car_filter)

    total = collector.count(query, sort)
    print(f'총 {total}개의 차량을 검색합니다.')

    cars = []
    for listing in tqdm(collector.fetch_listings(query, sort, total)):
        car = collector.inspect(listing, len(cars) + 1)
        if car:
            cars.append(car)

    summary = (
        f'총 {total}개의 결과에서 영업용도 사용 이력이 없고 '
        f'명의 변경 횟수가 {car_filter.max_owner_change_cnt}회 이하인 차 {len(cars)}대입니다.'
    )
    created_at = datetime.now()
    output_path = _build_output_path(file_name, created_at)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(render_report(file_name, summary, cars, created_at))

    print(f'파일 생성이 완료되었습니다. ({output_path})')


def _build_output_path(file_name, created_at=None):
    os.makedirs(RESULT_DIR, exist_ok=True)
    timestamp = (created_at or datetime.now()).strftime('%Y-%m-%d_%H_%M_%S')
    return os.path.join(RESULT_DIR, f'{timestamp}_{file_name}.html')
