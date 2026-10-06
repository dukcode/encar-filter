"""필터 결과를 정렬 가능한 HTML 문서로 렌더링."""
import html
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / 'templates' / 'report.html'


def render_report(title, summary, cars):
    """정렬 가능한 HTML 테이블 문서 생성 (기본 정렬: 가격 오름차순)"""
    rows = [
        _render_row(rank, car)
        for rank, car in enumerate(sorted(cars, key=lambda car: car.price), 1)
    ]
    return (TEMPLATE_PATH.read_text(encoding='utf-8')
            .replace('__TITLE__', html.escape(title))
            .replace('__SUMMARY__', html.escape(summary))
            .replace('__ROWS__', '\n'.join(rows)))


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


def _render_row(rank, car):
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
        f'<td data-value="{rank}">'
        f'<a href="{html.escape(car.detail_url, quote=True)}" target="_blank" rel="noopener">보기</a>'
        '</td>'
        '</tr>'
    )
