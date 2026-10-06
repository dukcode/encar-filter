"""엔카 URL 파싱과 생성."""
import json
from urllib.parse import quote, unquote

SEARCH_API = 'https://api.encar.com/search/car/list/general'
VEHICLE_API = 'https://api.encar.com/v1/readside/vehicle'
RECORD_API = 'https://api.encar.com/v1/readside/record/vehicle'
DETAIL_PAGE = 'https://fem.encar.com/cars/detail'
PICTURE_BASE = 'https://ci.encar.com/carpicture'

DEFAULT_SORT = 'ModifiedDate'


class InvalidPageUrlError(ValueError):
    """검색 조건(`#!` fragment)이 없는 페이지 URL."""


def parse_page_url(page_url):
    """엔카 페이지 URL에서 검색 쿼리와 정렬 기준을 추출"""
    fragment_idx = page_url.find('#!')
    if fragment_idx == -1:
        raise InvalidPageUrlError(
            'URL에서 검색 조건을 찾을 수 없습니다. 엔카 검색 결과 페이지 URL을 입력해주세요.'
        )
    params = json.loads(unquote(page_url[fragment_idx + 2:]))
    return params.get('action', ''), params.get('sort', DEFAULT_SORT)


def build_search_api_url(query, sort, offset, count):
    """검색 목록 API URL 생성"""
    encoded_query = quote(query, safe='()._')
    return (
        f'{SEARCH_API}'
        f'?count=true'
        f'&q={encoded_query}'
        f'&sr=%7C{sort}%7C{offset}%7C{count}'
        f'&inav=%7CMetadata%7CSort'
    )


def build_vehicle_api_url(car_id):
    """차량 기본 정보 API URL 생성"""
    return f'{VEHICLE_API}/{car_id}'


def build_record_api_url(car_id, vehicle_no):
    """보험 이력 API URL 생성"""
    return f'{RECORD_API}/{car_id}/open?vehicleNo={quote(vehicle_no)}'


def build_detail_url(car_id, position=1):
    """상세 페이지 URL 생성"""
    return (
        f'{DETAIL_PAGE}/{car_id}'
        f'?pageid=fc_carsearch&listAdvType=normal&carid={car_id}&view_type=hs_ad'
        f'&adv_attribute=hs_ad&wtClick_forList=019'
        f'&advClickPosition=imp_normal_p1_g{position}'
    )


def build_thumbnail_url(photos):
    """차량 정보 API의 실제 사진 경로로 대표 외관 썸네일 URL 생성."""
    available = [photo for photo in (photos or []) if photo.get('path')]
    if not available:
        return None
    photo = next((photo for photo in available if photo.get('code') == '001'), None)
    if photo is None:
        photo = next((photo for photo in available if photo.get('type') == 'OUTER'), available[0])
    path = quote(photo['path'].lstrip('/'), safe='/')
    url = (
        f'{PICTURE_BASE}/{path}'
        '?impolicy=heightRate&rh=192&cw=320&ch=192&cg=Center'
        '&wtmk=https://ci.encar.com/wt_mark/w_mark_04.png'
        '&wtmkg=SouthEast&wtmkw=70&wtmkh=30'
    )
    if photo.get('updateDateTime'):
        url += '&t=' + quote(photo['updateDateTime'], safe='')
    return url
