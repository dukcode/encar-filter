"""엔카 API 호출."""
import requests

from . import urls

PAGE_SIZE = 50


class EncarApi:
    """엔카 오픈 API에 대한 얇은 HTTP 클라이언트."""

    def __init__(self, session=None):
        self._session = session or requests.Session()

    def search(self, query, sort, offset, count=PAGE_SIZE):
        """검색 결과 한 페이지 (전체 건수 `Count` 포함)"""
        response = self._session.get(urls.build_search_api_url(query, sort, offset, count))
        response.raise_for_status()
        return response.json()

    def fetch_vehicle(self, car_id):
        """차량 기본 정보 (vehicleNo 포함). 조회 실패 시 None"""
        return self._get_json(urls.build_vehicle_api_url(car_id))

    def fetch_record(self, car_id, vehicle_no):
        """보험 이력 정보 (용도 이력, 명의 변경, 사고 이력 등). 조회 실패 시 None"""
        return self._get_json(urls.build_record_api_url(car_id, vehicle_no))

    def _get_json(self, url):
        response = self._session.get(url)
        if response.status_code != 200:
            return None
        return response.json()
