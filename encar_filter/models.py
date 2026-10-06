"""도메인 데이터 구조."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CarListing:
    """검색 결과 목록에 실린 매물 한 건."""

    car_id: str
    price: int  # 만원
    mileage: int  # km


@dataclass(frozen=True)
class InspectedCar:
    """보험 이력까지 조회해 필터를 통과한 매물."""

    listing: CarListing
    owner_change_cnt: int
    accident_cnt: int
    avg_accident_cost: int  # 사고 1건당 평균 피해액 (만원)
    detail_url: str
    year: Optional[int] = None  # 보험 이력의 연식 (등록 연월과 다름)
    thumbnail_url: Optional[str] = None

    @property
    def price(self):
        return self.listing.price

    @property
    def mileage(self):
        return self.listing.mileage
