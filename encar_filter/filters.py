"""보험 이력(record) 해석과 필터 조건."""
from dataclasses import dataclass

UNKNOWN_OWNER_CHANGE_CNT = 999


def is_commercial_use(record_info):
    """렌트카/영업용 여부 확인"""
    if not record_info:
        return False
    # government: 관용, business: 영업용, loan: 대여
    return record_info.get('government', 0) > 0 or \
           record_info.get('business', 0) > 0 or \
           record_info.get('loan', 0) > 0


def owner_change_cnt(record_info):
    """명의 변경 횟수 (조회 실패 시 필터에서 걸리도록 큰 값)"""
    if not record_info:
        return UNKNOWN_OWNER_CHANGE_CNT
    return record_info.get('ownerChangeCnt', UNKNOWN_OWNER_CHANGE_CNT)


def accident_info(record_info):
    """사고 정보 (횟수, 총 피해액)"""
    if not record_info:
        return 0, 0
    return record_info.get('myAccidentCnt', 0), record_info.get('myAccidentCost', 0)


def avg_accident_cost(record_info):
    """사고 1건당 평균 피해액 (만원)"""
    cnt, cost = accident_info(record_info)
    if cnt <= 0:
        return 0
    return cost // cnt // 10000


@dataclass(frozen=True)
class CarFilter:
    """보험 이력 기준 매물 필터."""

    max_owner_change_cnt: int = 2
    exclude_commercial: bool = True

    def accepts(self, record_info):
        """보험 이력이 필터 조건을 만족하는지 여부"""
        if self.exclude_commercial and is_commercial_use(record_info):
            return False
        return owner_change_cnt(record_info) <= self.max_owner_change_cnt
