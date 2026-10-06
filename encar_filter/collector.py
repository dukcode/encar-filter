"""검색 → 상세 조회 → 필터링 파이프라인."""
from .api import PAGE_SIZE
from .filters import CarFilter, accident_info, avg_accident_cost, car_year, owner_change_cnt
from .models import CarListing, InspectedCar
from .urls import build_detail_url, build_thumbnail_url


class CarCollector:
    """검색 조건에 해당하는 매물을 모아 필터를 통과한 차량만 남긴다."""

    def __init__(self, api, car_filter=None):
        self._api = api
        self._filter = car_filter or CarFilter()

    def count(self, query, sort):
        """검색 조건에 해당하는 전체 매물 수"""
        return int(self._api.search(query, sort, 0)['Count'])

    def fetch_listings(self, query, sort, total):
        """전체 매물 목록을 페이징하며 수집"""
        listings = []
        for offset in range(0, total + 1, PAGE_SIZE):
            data = self._api.search(query, sort, offset)
            for car_data in data['SearchResults']:
                listings.append(CarListing(
                    car_id=car_data['Id'],
                    price=int(car_data['Price']),
                    mileage=int(car_data['Mileage']),
                ))
        return listings

    def inspect(self, listing, position):
        """매물의 보험 이력을 조회해 필터를 통과하면 InspectedCar, 아니면 None"""
        vehicle_info = self._api.fetch_vehicle(listing.car_id)
        if not vehicle_info:
            return None

        vehicle_no = vehicle_info.get('vehicleNo')
        if not vehicle_no:
            return None

        record_info = self._api.fetch_record(listing.car_id, vehicle_no)
        if not self._filter.accepts(record_info):
            return None

        return InspectedCar(
            listing=listing,
            owner_change_cnt=owner_change_cnt(record_info),
            accident_cnt=accident_info(record_info)[0],
            avg_accident_cost=avg_accident_cost(record_info),
            detail_url=build_detail_url(listing.car_id, position),
            year=car_year(record_info),
            thumbnail_url=build_thumbnail_url(vehicle_info.get('photos')),
        )
