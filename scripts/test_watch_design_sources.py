from datetime import date
import unittest

from watch_design_sources import CSSDA, read_css_award, source_result


TODAY = date(2026, 11, 22)
WINNER = "/sites/ink-in-motion/12345/"
HOME = f'<h3 class="home-wotd__title"><a href="{WINNER}">Ink &amp; Motion</a></h3>'


class CSSDesignAwardsTest(unittest.TestCase):
    def test_reads_the_award_date_and_canonical_link(self):
        pages = {
            f"{CSSDA}/": HOME,
            CSSDA + WINNER: '<h1 class="single-website__date">Website Of The Day 2026 Nov 21</h1>',
        }
        self.assertEqual(
            read_css_award(TODAY, pages.__getitem__),
            [{"title": "Ink & Motion", "date": "2026-11-21", "url": CSSDA + WINNER}],
        )

    def test_reports_missing_or_ineligible_award_dates(self):
        for detail in ("No winner yet", "Website Of The Day 2026 Nov 10", "Website Of The Day 2026 Nov 23"):
            with self.subTest(detail=detail):
                pages = {
                    f"{CSSDA}/": HOME,
                    CSSDA + WINNER: f'<h1 class="single-website__date">{detail}</h1>',
                }
                self.assertEqual(
                    source_result("CSSDA", read_css_award, TODAY, pages.__getitem__),
                    {"source": "CSSDA", "error": "ValueError"},
                )

    def test_ignores_a_link_outside_the_official_award_path(self):
        pages = {f"{CSSDA}/": HOME.replace(WINNER, "https://example.test/")}
        with self.assertRaisesRegex(ValueError, "link was not found"):
            read_css_award(TODAY, pages.__getitem__)
