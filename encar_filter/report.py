"""필터 결과를 정렬 가능한 HTML 문서로 렌더링."""
import html
from datetime import date, datetime
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / 'templates' / 'report.html'


def render_report(title, summary, cars, created_at=None):
    """정렬 가능한 HTML 테이블 문서 생성 (기본 정렬: 가격 오름차순)"""
    created_at = created_at or datetime.now()
    rows = [
        _render_row(rank, car, created_at.date())
        for rank, car in enumerate(sorted(cars, key=lambda car: car.price), 1)
    ]
    return (TEMPLATE_PATH.read_text(encoding='utf-8')
            .replace('__TITLE__', html.escape(title))
            .replace('__SUMMARY__', html.escape(summary))
            .replace('__CREATED_AT__', created_at.strftime('%Y-%m-%d %H:%M:%S'))
            .replace('__ROWS__', '\n'.join(rows)))


def _annual_mileage_range(mileage, year, created_on):
    """연식의 첫날/마지막 날부터 생성일까지의 기간으로 연평균 범위를 추정."""
    if year is None or not 1 <= year <= 9999 or mileage < 0:
        return None
    longest_days = (created_on - date(year, 1, 1)).days
    shortest_days = (created_on - date(year, 12, 31)).days
    if shortest_days <= 0:
        return None
    return mileage * 365.25 / longest_days, mileage * 365.25 / shortest_days


def _render_annual_mileage(car, created_on):
    bounds = _annual_mileage_range(car.mileage, car.year, created_on)
    if bounds is None:
        label = '미확인' if car.year is None else '계산 불가'
        return f'<td data-value="" data-annual-mileage="">{label}</td>'
    lower, upper = bounds
    # 화면에 보이는 중앙값과 필터 경계가 일치하도록 1km/년 단위로 반올림한다.
    midpoint = round((lower + upper) / 2)
    return (
        f'<td data-value="{midpoint}" data-annual-mileage="{midpoint}">'
        f'{lower:,.0f}~{upper:,.0f}km/년'
        f'<span class="annual-midpoint">중앙값 {midpoint:,}km/년</span></td>'
    )


def _render_thumbnail(car):
    if not car.thumbnail_url:
        return '<td class="thumbnail-cell"><span class="thumbnail-placeholder">사진 없음</span></td>'
    car_id = html.escape(str(car.listing.car_id), quote=True)
    return (
        '<td class="thumbnail-cell">'
        f'<a class="thumbnail-link" href="{html.escape(car.detail_url, quote=True)}" '
        f'target="_blank" rel="noopener" aria-label="매물 {car_id} 상세 보기">'
        f'<img src="{html.escape(car.thumbnail_url, quote=True)}" '
        f'alt="매물 {car_id} 사진" width="160" height="96" loading="lazy" decoding="async" '
        'onerror="this.hidden = true; this.nextElementSibling.hidden = false;">'
        '<span class="thumbnail-placeholder" hidden>사진 없음</span></a></td>'
    )


def _render_row(rank, car, created_on):
    return (
        '<tr>'
        f'<td data-value="{rank}">{rank}</td>'
        f'{_render_thumbnail(car)}'
        f'<td data-value="{car.year if car.year is not None else ""}">'
        f'{str(car.year) + "년식" if car.year is not None else "미확인"}</td>'
        f'<td data-value="{car.owner_change_cnt}">{car.owner_change_cnt}회</td>'
        f'<td data-value="{car.price}">{car.price:,}만원</td>'
        f'<td data-value="{car.accident_cnt}">{car.accident_cnt}회</td>'
        f'<td data-value="{car.avg_accident_cost}">{car.avg_accident_cost:,}만원</td>'
        f'<td data-value="{car.mileage}">{car.mileage:,}km</td>'
        f'{_render_annual_mileage(car, created_on)}'
        f'<td data-value="{rank}">'
        f'<a href="{html.escape(car.detail_url, quote=True)}" target="_blank" rel="noopener">보기</a>'
        '</td>'
        '</tr>'
    )
