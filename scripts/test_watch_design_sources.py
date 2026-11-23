from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from io import StringIO
import unittest
from urllib.parse import parse_qs, urlsplit

from watch_design_sources import (
    AWWWARDS, CSSDA, HN_API, print_report, read_awwwards, read_css_award, read_show_hn,
    read_top_hn, source_result,
)


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


class AwwwardsTest(unittest.TestCase):
    HEADER = (
        '<a href="/sites/unrelated">Unrelated</a><div class="anchor-section" id="sotd">'
        '<a class="item-link" href="/sites/ink-in-motion" aria-label="Ink &amp; Motion"></a>'
        '<h2><span>Site of the Day</span>\n<strong class="budget-tag">Nov 22, 2026</strong></h2>'
        '<h1 class="heading-1">Ink &amp; Motion</h1></div>'
    )

    def test_reads_the_winner_from_its_dated_header(self):
        self.assertEqual(read_awwwards(TODAY, {f"{AWWWARDS}/": self.HEADER}.__getitem__), [
            {"title": "Ink & Motion", "date": "2026-11-22", "url": f"{AWWWARDS}/sites/ink-in-motion"},
        ])

    def test_rejects_undated_stale_future_and_offsite_candidates(self):
        for page in (
            self.HEADER.replace('id="sotd"', 'id="nominees"'),
            self.HEADER.replace("Nov 22, 2026", ""),
            self.HEADER.replace("Nov 22, 2026", "Nov 14, 2026"),
            self.HEADER.replace("Nov 22, 2026", "Nov 23, 2026"),
            self.HEADER.replace("/sites/ink-in-motion", "//example.test/sites/ink-in-motion"),
        ):
            with self.subTest(page=page):
                self.assertEqual(
                    source_result("Awwwards", read_awwwards, TODAY, lambda _: page),
                    {"source": "Awwwards", "error": "ValueError"},
                )


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

    def test_retains_an_interactive_calculator_from_its_description(self):
        timestamp = int(datetime(2026, 11, 22, tzinfo=timezone.utc).timestamp())

        def fetch(url):
            if url == f"{HN_API}/showstories.json":
                return [1, 2]
            item_id = 1 if url.endswith("/1.json") else 2
            return {
                "id": item_id, "type": "story", "time": timestamp, "score": 4,
                "title": "Show HN: A machining reference",
                "text": "Try the speeds and feeds calculator." if item_id == 1 else "Read the reference.",
            }

        self.assertEqual(
            [item["url"] for item in read_show_hn(TODAY, fetch)],
            ["https://news.ycombinator.com/item?id=1"],
        )


class SocialLeadTest(unittest.TestCase):
    def test_report_links_to_searches_with_original_queries(self):
        output = StringIO()
        with redirect_stdout(output):
            print_report([])
        links = [line.split("](", 1)[1][:-1] for line in output.getvalue().splitlines()
                 if line.startswith("- [") and ("https://x.com/" in line or "reddit.com/" in line)]
        targets = [urlsplit(link) for link in links]
        self.assertEqual([target.netloc for target in targets], ["x.com"] * 8 + ["www.reddit.com"])
        queries = [parse_qs(target.query) for target in targets]
        self.assertEqual(queries[0]["q"], ["UI design filter:images min_faves:200"])
        self.assertEqual(queries[-2]["q"], ["product design breakdown filter:images min_faves:150"])
        self.assertEqual(queries[-1]["t"], ["week"])
        self.assertIn("https://muuuuu.org/en/", output.getvalue())


class FrontPageHNTest(unittest.TestCase):
    def test_recovers_visual_projects_without_double_counting_show_hn(self):
        timestamp = int(datetime(2026, 11, 22, tzinfo=timezone.utc).timestamp())
        titles = {
            2: ("A miniature San Francisco with live buses, planes and boats", "https://smallsf.com/"),
            5: ("Sandwich Simulator", "https://stulle.app/"),
            9: ("Show HN: Flight simulator", "https://example.test/"),
            13: ("Notes on the discrete Fourier transform", "https://example.test/"),
            15: ("Interactive map", "http://example.test/"),
            21: ("Miniature city simulator", "https://example.test/"),
        }

        def fetch(url):
            if url == f"{HN_API}/topstories.json":
                return list(range(1, 25))
            item_id = int(url.rsplit("/", 1)[-1].removesuffix(".json"))
            self.assertLessEqual(item_id, 20)
            title, target = titles.get(item_id, ("Unrelated article", "https://example.test/"))
            return {"id": item_id, "type": "story", "time": timestamp, "title": title,
                    "url": target, "score": 100 + item_id, "descendants": 2}

        self.assertEqual(
            [item["url"] for item in read_top_hn(TODAY, fetch)],
            ["https://news.ycombinator.com/item?id=5", "https://news.ycombinator.com/item?id=2"],
        )
