from datetime import date, datetime, timezone
import unittest

from watch_design_sources import CSSDA, HN_API, read_css_award, read_show_hn, source_result


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


class ShowHNTest(unittest.TestCase):
    def test_reads_past_the_top_ten_and_searches_the_creator_description(self):
        timestamp = int(datetime(2026, 11, 22, tzinfo=timezone.utc).timestamp())

        def fetch(url):
            if url == f"{HN_API}/showstories.json":
                return list(range(1, 40))
            item_id = int(url.rsplit("/", 1)[-1].removesuffix(".json"))
            self.assertLessEqual(item_id, 30)
            if item_id == 1:
                raise OSError("temporary fetch failure")
            return {
                "id": item_id, "type": "story", "time": timestamp,
                "title": "Show HN: You Are Hilbert" if item_id == 16 else "Show HN: Other",
                "text": "A <em>star map</em> of the internet." if item_id == 16 else "",
                "score": 8, "descendants": 3,
            }

        self.assertEqual(read_show_hn(TODAY, fetch), [{
            "title": "Show HN: You Are Hilbert", "date": "2026-11-22",
            "url": "https://news.ycombinator.com/item?id=16", "points": 8, "comments": 3,
        }])
