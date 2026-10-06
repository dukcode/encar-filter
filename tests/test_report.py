import unittest
from datetime import date, datetime
from html.parser import HTMLParser
from tempfile import TemporaryDirectory
from unittest.mock import patch

from encar_filter.cli import _build_output_path
from encar_filter.models import CarListing, InspectedCar
from encar_filter.report import _annual_mileage_range, render_report


class ReportParser(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.rows = []
        self.in_body = False
        self.cell = None
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        if tag == 'tbody':
            self.in_body = True
        elif tag == 'tr' and self.in_body:
            self.rows.append([])
        elif tag == 'td' and self.in_body:
            self.cell = {'attrs': dict(attrs), 'text': ''}
            self.rows[-1].append(self.cell)

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'] += data

    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_body = False
        elif tag == 'td':
            self.cell = None


def car(year=2018, mileage=80000, price=1000):
    return InspectedCar(CarListing('123', price, mileage), 1, 0, 0,
                        'https://example.com/?a=1&b=2', year)


class AnnualMileageTest(unittest.TestCase):
    def test_range_uses_entire_model_year(self):
        lower, upper = _annual_mileage_range(80000, 2018, date(2020, 1, 1))
        # Jan 1, 2018 is 730 days ago; Dec 31 is 366 days ago.
        self.assertAlmostEqual(lower, 40027.39726027397)
        self.assertAlmostEqual(upper, 79836.0655737705)
        self.assertLess(lower, upper)

    def test_leap_year_and_one_day_old_latest_possible_date(self):
        lower, upper = _annual_mileage_range(366, 2020, date(2021, 1, 1))
        self.assertEqual(lower, 365.25)
        self.assertEqual(upper, 133681.5)

    def test_zero_mileage_is_known_zero(self):
        self.assertEqual(_annual_mileage_range(0, 2018, date(2026, 10, 4)), (0, 0))

    def test_unknown_invalid_and_not_yet_elapsed_years_are_unavailable(self):
        for year in (None, 0, 10000, 2026, 2027):
            with self.subTest(year=year):
                self.assertIsNone(_annual_mileage_range(10000, year, date(2026, 10, 4)))
        self.assertIsNone(_annual_mileage_range(10000, 2025, date(2025, 12, 31)))
        self.assertIsNone(_annual_mileage_range(-1, 2018, date(2026, 10, 4)))

    def test_report_uses_fixed_creation_date_and_midpoint_for_sort_and_filter(self):
        document = render_report('A&B', '<summary>', [car()], datetime(2020, 1, 1, 23, 59, 59))
        annual = ReportParser(document).rows[0][8]
        self.assertEqual(annual['text'], '40,027~79,836km/년중앙값 59,932km/년')
        self.assertEqual(annual['attrs']['data-value'], '59932')
        self.assertEqual(annual['attrs']['data-annual-mileage'], '59932')
        self.assertIn('파일 생성일: 2020-01-01 23:59:59', document)
        self.assertIn('<title>A&amp;B</title>', document)
        self.assertIn('&lt;summary&gt;', document)
        self.assertNotIn('__CREATED_AT__', document)

    def test_price_order_and_unavailable_cells_are_preserved(self):
        document = render_report('test', '', [car(None, price=2000), car(2026), car(mileage=0, price=3000)],
                                 datetime(2026, 10, 4))
        rows = ReportParser(document).rows
        self.assertEqual([row[4]['attrs']['data-value'] for row in rows], ['1000', '2000', '3000'])
        self.assertTrue(all(len(row) == 10 for row in rows))
        self.assertEqual([row[8]['attrs']['data-value'] for row in rows], ['', '', '0'])
        self.assertEqual(rows[0][8]['text'], '계산 불가')
        self.assertEqual(rows[1][8]['text'], '미확인')
        self.assertEqual(rows[2][8]['text'], '0~0km/년중앙값 0km/년')

    def test_empty_report(self):
        document = render_report('test', '', [], datetime(2026, 10, 4))
        self.assertEqual(ReportParser(document).rows, [])

    def test_filename_uses_supplied_creation_time(self):
        with TemporaryDirectory() as directory, patch('encar_filter.cli.RESULT_DIR', directory):
            path = _build_output_path('test', datetime(2026, 10, 4, 21, 1, 33))
            self.assertTrue(path.endswith('/2026-10-04_21_01_33_test.html'))


if __name__ == '__main__':
    unittest.main()
