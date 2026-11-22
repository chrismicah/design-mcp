"""Focused tests for the local page review.

They need no third-party packages:  python -m unittest tests.test_review -v

The board below is a hand-written capture in the page-evidence format, shaped like the rehearsal-room
board in the benchmark briefs. It is test input, not a recorded result from a real page.
"""

import base64
import contextlib
import hashlib
import io
import json
import os
import re
import stat
import struct
import subprocess
import sys
import tempfile
import tomllib
import unittest
import zlib
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

from design_mcp.design_checks import inspect_design
from design_mcp.review import SCHEMA, address, checks, cli, evidence, host, isolated, pipeline, preview, review

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "design_mcp" / "review" / "extension"
EXTENSION_ID = "abcdefghijklmnop" * 2
ORIGIN = f"chrome-extension://{EXTENSION_ID}/"
PAPER = [246, 245, 241]
PALE = [154, 160, 166, 1]
SEEDS = (
    "SEEDED-FIELD-VALUE-91", "SEEDED-QUERY-TOKEN-92", "SEEDED-FRAGMENT-93",
    "SEEDED-PASSWORD-94", "SEEDED-RAW-CONTENT-95", "SEEDED-PNG-TEXT-96",
)
_VOID = frozenset("area base br col embed hr img input link meta source track wbr".split())


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def png(width=4, height=3, rgb=(246, 245, 241), extra=b""):
    rows = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + extra
            + _chunk(b"IDAT", zlib.compress(rows)) + _chunk(b"IEND", b""))


def region(name, y, **overrides):
    base = {
        "role": "text",
        "name": name,
        "landmark": "main",
        "heading": "Rehearsal rooms",
        "locator": "main > p",
        "reading_order": 1,
        "box": {"x": 0.1, "y": y, "width": 0.5, "height": 0.05},
        "font": {"family": "IBM Plex Sans", "size_px": 16, "weight": 400},
        "ink": [22, 24, 29, 1],
        "fill": [246, 245, 241, 1],
        "fill_flat": True,
        "has_text": True,
    }
    base.update(overrides)
    return base


def board(**capture):
    """A 390 px view with one hard-to-read line: the pale room count."""
    regions = [
        region("Rehearsal rooms", 0.06, id="r1", role="heading", reading_order=1,
               font={"family": "Newsreader", "size_px": 53, "weight": 600}),
        region("Delayed only", 0.2832, id="r2", role="button", reading_order=2, pressed="false",
               box={"x": 0.3538, "y": 0.2832, "width": 0.3026, "height": 0.0521},
               font={"family": "IBM Plex Sans", "size_px": 15, "weight": 600}),
        region("Studio B", 0.4, id="r3", role="rowheader", reading_order=3),
        region("6 minutes late", 0.46, id="r4", reading_order=4, ink=[255, 255, 255, 1], fill=[122, 28, 46, 1]),
        region("2 of 2 rooms", 0.52, id="r5", role="status", reading_order=5, ink=list(PALE)),
    ]
    return {
        "schema": SCHEMA,
        "capture": {
            "source": "active-tab",
            "url": "https://boards.example/rooms?day=today",
            "title": "Rehearsal rooms",
            "captured_at": "2026-11-21T22:41:00Z",
            "user_triggered": True,
            **capture,
        },
        "frames": [{
            "viewport": {"width": 390, "height": 844, "dpr": 2},
            "document": {"scroll_width": 390, "client_width": 390, "lang": "en"},
            "screenshot": {"media_type": "image/png", "data": base64.b64encode(png()).decode("ascii")},
            "regions": regions,
            "primary_control": {"region": "r2", "basis": "first button inside the main content", "covered_by": None},
            "masks": {"applied": True, "boxes": []},
        }],
        "timings_ms": {"capture": 212},
    }


def wide_board():
    bundle = board()
    frame = bundle["frames"][0]
    frame["document"].update(scroll_width=428, client_width=390)
    frame["overflow"] = {
        "name": "Call sheet table",
        "locator": "main > table",
        "box": {"x": 0.04, "y": 0.36, "width": 1.06, "height": 0.3},
    }
    return bundle


def kinds(findings):
    return [finding["check"] for finding in findings]


def no_lookup(*_args, **_kwargs):
    raise AssertionError("no name lookup is expected here")


def framed(message):
    data = json.dumps(message).encode("utf-8")
    return struct.pack("=I", len(data)) + data


def unframed(data):
    (size,) = struct.unpack("=I", data[:4])
    assert size == len(data) - 4, (size, len(data))
    return json.loads(data[4:].decode("utf-8"))


class Page(HTMLParser):
    """Every element with its attributes, and whether it sits inside something marked hidden."""

    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.elements, self.styles, self._open = [], [], []
        self.feed(document)
        self.close()

    @property
    def tags(self):
        return [(tag, attrs) for tag, attrs, _ in self.elements]

    def named(self, name, **wanted):
        return [attrs for tag, attrs in self.tags
                if tag == name and all(attrs.get(key) == value for key, value in wanted.items())]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = "hidden" in attrs or any(flag for _, flag in self._open)
        self.elements.append((tag, attrs, hidden))
        if tag not in _VOID:
            self._open.append((tag, hidden))

    def handle_endtag(self, tag):
        for index in range(len(self._open) - 1, -1, -1):
            if self._open[index][0] == tag:
                del self._open[index:]
                break

    def handle_data(self, data):
        if self._open and self._open[-1][0] == "style":
            self.styles.append(data)


class AddressTests(unittest.TestCase):
    def test_stored_address_drops_sign_in_details_tokens_and_fragment(self):
        clean, removed = evidence.inspect_url(
            "https://chris:SEEDED-PASSWORD-94@Boards.Example:443/rooms"
            "?day=today&access_token=SEEDED-QUERY-TOKEN-92#SEEDED-FRAGMENT-93")
        self.assertEqual(clean, "https://boards.example/rooms?day=today")
        self.assertEqual(len(removed), 2)
        for key in ("apiKey", "X-Amz-Signature", "PHPSESSID", "id_token", "sig", "code"):
            with self.subTest(key=key):
                self.assertEqual(evidence.scrub_url(f"https://boards.example/a?{key}=1&page=2"),
                                 "https://boards.example/a?page=2")

    def test_long_random_values_are_dropped_even_under_plain_names(self):
        self.assertEqual(evidence.scrub_url("https://boards.example/?ref=a1B2c3D4e5F6g7H8i9J0k1L2m3"),
                         "https://boards.example/")
        self.assertEqual(evidence.scrub_url("https://boards.example/?q=how-to-read-a-rehearsal-call-sheet"),
                         "https://boards.example/?q=how-to-read-a-rehearsal-call-sheet")

    def test_only_web_pages_are_accepted(self):
        for url in ("data:text/html,<h1>x</h1>", "file:///etc/hosts", "javascript:alert(1)", "chrome://extensions",
                    "about:blank", "blob:https://a.example/1", "https://", "", None):
            with self.subTest(url=url):
                with self.assertRaises(evidence.EvidenceError) as caught:
                    evidence.inspect_url(url)
                self.assertEqual(caught.exception.code, "unsupported-url")

    def test_pasted_addresses_must_look_public(self):
        for url in ("http://localhost:3000/", "http://127.0.0.1/", "http://10.0.0.8/", "http://192.168.1.1/admin",
                    "http://169.254.169.254/latest", "http://[::1]/", "http://intranet/", "http://printer.local/"):
            with self.subTest(url=url):
                self.assertEqual(address.local_address_reason(url), address.NOT_PUBLIC)
        self.assertIsNone(address.local_address_reason("https://boards.example/rooms"))
        self.assertIsNone(address.local_address_reason("https://93.184.216.34/"))

    def test_a_public_name_that_points_at_a_private_address_is_refused(self):
        def resolver(_host, port, type=None):
            return [(2, 1, 6, "", ("10.1.2.3", port))]

        with self.assertRaises(evidence.EvidenceError) as caught:
            address.public_target("https://boards.example/", resolve=resolver)
        self.assertEqual(caught.exception.code, "private-address")

    def test_a_public_target_is_pinned_to_the_address_that_was_checked(self):
        def resolver(_host, port, type=None):
            return [(30, 1, 6, "", ("2606:2800:220:1:248:1893:25c8:1946", port, 0, 0)),
                    (2, 1, 6, "", ("93.184.216.34", port))]

        self.assertEqual(address.public_target("https://Boards.Example/rooms#top", resolve=resolver),
                         ("https://boards.example/rooms", "boards.example", "93.184.216.34"))

    def test_pasted_addresses_with_sign_in_details_are_refused_before_any_lookup(self):
        for url in ("https://boards.example/?token=abc", "https://chris:pw@boards.example/"):
            with self.subTest(url=url):
                with self.assertRaises(evidence.EvidenceError) as caught:
                    address.public_target(url, resolve=no_lookup)
                self.assertEqual(caught.exception.code, "credentials-in-url")


class EvidenceTests(unittest.TestCase):
    def test_missing_fields_are_marked_unknown_and_boxes_are_clipped_to_the_view(self):
        bundle = board()
        bundle["frames"][0]["regions"].append({"box": {"x": 0.9, "y": 0.9, "width": 0.5, "height": 0.5}})
        bundle["frames"][0]["regions"].append({"name": "Below the fold", "box": {"x": 0.1, "y": 1.2, "width": 0.5, "height": 0.1}})
        clean = evidence.normalize(bundle)
        frame = clean["frames"][0]
        self.assertEqual(len(frame["regions"]), 6)
        bare = frame["regions"][-1]
        self.assertEqual(bare["id"], "r6")
        self.assertEqual(bare["box"], {"x": 0.9, "y": 0.9, "width": 0.1, "height": 0.1})
        for key in ("role", "name", "landmark", "heading", "locator", "reading_order", "ink", "fill", "fill_flat", "pressed"):
            self.assertEqual(bare[key], "unknown", key)
        self.assertEqual(bare["font"], {"family": "unknown", "size_px": "unknown", "weight": "unknown"})
        self.assertEqual(clean["schema"], "design-mcp.page-evidence/1")
        self.assertEqual((frame["id"], frame["state"], frame["viewport"]), ("f1", "initial", {"width": 390, "height": 844, "dpr": 2}))
        self.assertRegex(clean["capture"]["id"], r"^c-[0-9a-f]{12}$")
        self.assertEqual(clean["timings_ms"], {"page_load": "unknown", "capture": 212})

    def test_at_most_eight_regions_are_kept_per_view(self):
        bundle = board()
        bundle["frames"][0]["regions"] = [region(f"Row {number}", 0.05 * number) for number in range(1, 12)]
        clean = evidence.normalize(bundle)
        self.assertEqual([item["id"] for item in clean["frames"][0]["regions"]], [f"r{number}" for number in range(1, 9)])
        self.assertIn("3 regions beyond the limit of 8", clean["notes"][0])

    def test_seeded_private_values_never_reach_the_reply_the_stored_files_or_the_picture(self):
        bundle = board(url="https://chris:SEEDED-PASSWORD-94@boards.example/rooms"
                           "?day=today&session=SEEDED-QUERY-TOKEN-92#SEEDED-FRAGMENT-93")
        frame = bundle["frames"][0]
        frame["regions"].append(region("Call notes", 0.7, id="r6", role="field", masked=True, has_text=False,
                                       value="SEEDED-FIELD-VALUE-91", text="SEEDED-FIELD-VALUE-91"))
        frame["regions"][2]["name"] = ("Studio B https://boards.example/share?sig=SEEDED-QUERY-TOKEN-92 "
                                       "data:text/plain;base64,SEEDED-RAW-CONTENT-95")
        frame["masks"] = {"applied": True, "boxes": [{
            "kind": "field", "box": {"x": 0.1, "y": 0.7, "width": 0.5, "height": 0.05}, "value": "SEEDED-FIELD-VALUE-91",
        }]}
        frame["html"] = "<main>SEEDED-RAW-CONTENT-95</main>"
        frame["screenshot"]["data"] = base64.b64encode(
            png(extra=_chunk(b"tEXt", b"Comment\x00SEEDED-PNG-TEXT-96"))).decode("ascii")
        bundle["cookies"] = "sid=SEEDED-QUERY-TOKEN-92"
        with tempfile.TemporaryDirectory() as folder:
            result = review(bundle, folder)
            self.assertTrue(result["ok"], result)
            stored = "".join(path.read_text(encoding="utf-8") for path in Path(folder).rglob("*") if path.is_file())
        clean = evidence.normalize(bundle)
        picture = base64.b64decode(clean["frames"][0]["screenshot"]["data"])
        self.assertEqual(picture, png())
        self.assertEqual(clean["capture"]["url"], "https://boards.example/rooms?day=today")
        self.assertEqual(clean["frames"][0]["regions"][2]["name"], "Studio B https://boards.example/share [removed]")
        self.assertEqual(result["masked"], {"field": 1, "editable": 0, "frame": 0})
        for seed in SEEDS:
            with self.subTest(seed=seed):
                self.assertNotIn(seed, stored)
                self.assertNotIn(seed, json.dumps(result))
                self.assertNotIn(seed, json.dumps(clean))
                self.assertNotIn(seed.encode("ascii"), picture)

    def test_fields_that_were_not_blanked_out_stop_the_capture(self):
        bundle = board()
        bundle["frames"][0]["masks"] = {"applied": False, "boxes": [
            {"kind": "field", "box": {"x": 0.1, "y": 0.7, "width": 0.5, "height": 0.05}}]}
        self.assertEqual(review(bundle, "unused")["code"], "private-data")
        bundle = board()
        bundle["frames"][0]["regions"].append(region("Call notes", 0.7, role="field", masked=True))
        del bundle["frames"][0]["masks"]
        self.assertEqual(review(bundle, "unused")["code"], "private-data")

    def test_captures_nobody_started_unsupported_pages_and_broken_pictures_are_refused(self):
        self.assertEqual(review(board(user_triggered=False), "unused")["code"], "not-user-triggered")
        self.assertEqual(review(board(url="file:///Users/someone/notes.html"), "unused")["code"], "unsupported-url")
        self.assertEqual(review(board(url="data:text/html,<p>hi</p>"), "unused")["code"], "unsupported-url")
        self.assertEqual(review({"schema": "other/9"}, "unused")["code"], "unsupported-schema")
        self.assertEqual(review(None, "unused")["code"], "unsupported-schema")
        broken = board()
        broken["frames"][0]["screenshot"]["data"] = base64.b64encode(b"GIF89a, not a PNG at all").decode("ascii")
        self.assertEqual(review(broken, "unused")["code"], "malformed")
        truncated = board()
        truncated["frames"][0]["screenshot"]["data"] = base64.b64encode(png()[:-12]).decode("ascii")
        self.assertEqual(review(truncated, "unused")["code"], "malformed")
        crowded = board()
        crowded["frames"] = crowded["frames"] * 5
        self.assertEqual(review(crowded, "unused")["code"], "too-large")
        self.assertFalse(Path("unused").exists())

    def test_an_interaction_is_kept_only_when_it_was_authorized(self):
        bundle = board()
        bundle["interaction"] = {"authorized": True, "key": "Enter", "target": "r2", "delta": {
            "focus": ["All rooms", "Delayed only"], "pressed": ["false", "true"], "visible_rows": [2, 1],
            "bounds_changed": True, "typed": "SEEDED-FIELD-VALUE-91",
        }}
        kept = evidence.normalize(bundle)["interaction"]
        self.assertEqual((kept["kind"], kept["key"], kept["target"]), ("keyboard-activation", "Enter", "r2"))
        self.assertEqual(kept["delta"], {
            "focus": ["All rooms", "Delayed only"], "pressed": ["false", "true"], "visible_rows": [2, 1],
            "bounds_changed": True,
        })
        bundle["interaction"]["authorized"] = False
        self.assertIsNone(evidence.normalize(bundle)["interaction"])


class CheckTests(unittest.TestCase):
    def test_contrast_math_matches_known_values(self):
        self.assertAlmostEqual(checks.contrast_ratio([0, 0, 0], [255, 255, 255]), 21.0, places=6)
        self.assertLess(checks.contrast_ratio([119, 119, 119], [255, 255, 255]), 4.5)
        self.assertGreaterEqual(checks.contrast_ratio([118, 118, 118], [255, 255, 255]), 4.5)
        self.assertEqual(checks.suggest_ink([119, 119, 119], [255, 255, 255]), [118, 118, 118])
        self.assertEqual(checks.suggest_ink([200, 200, 200], [0, 0, 0]), [200, 200, 200])

    def test_the_first_critique_names_the_region_the_problem_one_change_and_a_test(self):
        findings = checks.local_findings(evidence.normalize(board()))
        self.assertEqual(kinds(findings), ["contrast"])
        first = findings[0]
        self.assertEqual((first["frame"], first["region"], first["viewport"]), ("f1", "r5", "390x844"))
        self.assertEqual(first["box"], {"x": 0.1, "y": 0.52, "width": 0.5, "height": 0.05})
        self.assertTrue(first["problem"].startswith("“2 of 2 rooms” is hard to read at 390 px wide: its text color "
                                                    "#9aa0a6 on #f6f5f1 measures 2.4 to 1"), first["problem"])
        self.assertRegex(first["change"], r"^Change the text color of “2 of 2 rooms” from #9aa0a6 to #[0-9a-f]{6}\.$")
        self.assertIn("measures at least 4.5 to 1 against its background", first["outcome"])
        proposed = first["preview"]["to"]
        self.assertEqual(first["preview"]["from"], PALE[:3])
        self.assertGreaterEqual(checks.contrast_ratio(proposed, PAPER), 4.5)
        self.assertLess(checks.contrast_ratio(proposed, PAPER), 4.7)
        self.assertTrue(all(new <= old for new, old in zip(proposed, PALE)))
        self.assertTrue(2.4 <= first["evidence"]["ratio"] < 2.5, first["evidence"])
        self.assertGreaterEqual(first["evidence"]["proposed_ratio"], 4.5)

    def test_unknown_fills_and_disabled_or_blanked_regions_are_not_flagged(self):
        exempt = (
            {"fill_flat": False},
            {"fill_flat": "unknown"},
            {"fill": [246, 245, 241, 0.6]},
            {"fill": None},
            {"disabled": True},
            {"masked": True},
            {"has_text": False},
        )
        for override in exempt:
            bundle = board()
            bundle["frames"][0]["regions"] = [region("Pale note", 0.3, ink=list(PALE), **override)]
            with self.subTest(override=override):
                self.assertEqual(checks.local_findings(evidence.normalize(bundle)), [])

    def test_large_text_checks_three_to_one_and_keeps_normal_text_at_four_point_five(self):
        cases = (
            (24, 400, 145, 3.0),
            (18.667, 700, 145, 3.0),
            (24, 400, 140, None),
            (18.667, 700, 140, None),
            (23.99, 400, 140, 4.5),
            (18.66, 700, 140, 4.5),
            (18.667, 699, 140, 4.5),
        )
        for size, weight, gray, expected in cases:
            with self.subTest(size=size, weight=weight, gray=gray):
                bundle = board()
                font = {"family": "Newsreader", "size_px": size, "weight": weight}
                bundle["frames"][0]["regions"] = [
                    region("Collection details", 0.3, ink=[gray, gray, gray, 1], font=font)
                ]
                findings = checks.local_findings(evidence.normalize(bundle))
                if expected is None:
                    self.assertEqual(findings, [])
                    continue
                self.assertEqual(kinds(findings), ["contrast"])
                finding = findings[0]
                self.assertIn(f"{expected:g} to 1", finding["outcome"])
                self.assertGreaterEqual(checks.contrast_ratio(finding["preview"]["to"], PAPER), expected)

    def test_translucent_text_is_judged_by_the_color_it_shows_as(self):
        bundle = board()
        bundle["frames"][0]["regions"] = [region("Faded note", 0.3, ink=[22, 24, 29, 0.35])]
        finding = checks.local_findings(evidence.normalize(bundle))[0]
        self.assertEqual(finding["evidence"]["ink"], "#a8a8a7")
        self.assertEqual(finding["preview"]["from"], [168, 168, 167])

    def test_sideways_scroll_over_one_pixel_is_flagged_with_the_element_that_causes_it(self):
        bundle = wide_board()
        findings = checks.local_findings(evidence.normalize(bundle))
        self.assertEqual(kinds(findings), ["overflow", "contrast"])
        first = findings[0]
        self.assertEqual(first["problem"], "The page scrolls sideways by 38 px at 390 px wide because "
                                           "“Call sheet table” is wider than the screen.")
        self.assertIn("Keep “Call sheet table” inside the screen width", first["change"])
        self.assertIn("scrollWidth minus clientWidth is 1 px or less", first["outcome"])
        self.assertEqual(first["box"], {"x": 0.04, "y": 0.36, "width": 0.96, "height": 0.3})
        self.assertIsNone(first["preview"])
        bundle["frames"][0]["overflow"]["name"] = ""
        self.assertIn("the element at main > table", checks.local_findings(evidence.normalize(bundle))[0]["problem"])
        bundle["frames"][0]["document"].update(scroll_width=391)
        self.assertEqual(kinds(checks.local_findings(evidence.normalize(bundle))), ["contrast"])

    def test_a_fixed_bar_over_the_main_button_comes_first(self):
        bundle = board()
        bundle["frames"][0]["primary_control"]["covered_by"] = {
            "position": "fixed", "name": "Cookie notice", "locator": "#cookies",
            "box": {"x": 0, "y": 0.26, "width": 1, "height": 0.1}, "height_px": 84,
        }
        findings = checks.local_findings(evidence.normalize(bundle))
        self.assertEqual(kinds(findings), ["covered-control", "contrast"])
        first = findings[0]
        self.assertEqual(first["region"], "r2")
        self.assertTrue(first["problem"].startswith("“Cookie notice” stays on top of “Delayed only” at 390 px wide"))
        self.assertIn("add 84 px of space", first["change"])
        self.assertIn("is the button itself", first["outcome"])
        bundle["frames"][0]["primary_control"]["covered_by"]["position"] = "relative"
        self.assertEqual(kinds(checks.local_findings(evidence.normalize(bundle))), ["contrast"])


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.clean = evidence.normalize(board())
        self.findings = checks.local_findings(self.clean)
        self.document = preview.build_preview(self.clean, self.findings)
        self.page = Page(self.document)

    def assert_inert(self, document, page):
        names = [tag for tag, _ in page.tags]
        for banned in ("script", "iframe", "object", "embed", "link", "form", "a", "base", "img", "audio", "video", "button"):
            self.assertNotIn(banned, names)
        for tag, attrs in page.tags:
            for name, value in attrs.items():
                self.assertFalse(name.startswith("on"), (tag, name))
                self.assertNotEqual(name, "style", tag)
                if name in ("href", "src", "srcset", "action", "xlink:href", "poster", "data"):
                    self.assertTrue(value.startswith(("#", "data:image/png;base64,")), (tag, name, value[:48]))
        for needle in ("<script", "javascript:", "@import", "url(http", "url(//", "http-equiv=\"refresh\""):
            self.assertNotIn(needle, document)

    def test_the_preview_has_no_scripts_handlers_links_or_outside_resources(self):
        self.assert_inert(self.document, self.page)

    def test_the_policy_allows_only_the_capture_and_the_pinned_style_sheet(self):
        metas = self.page.named("meta")
        policy = next(attrs["content"] for attrs in metas if attrs.get("http-equiv") == "Content-Security-Policy")
        self.assertEqual(policy, preview.CSP)
        self.assertTrue(policy.startswith("default-src 'none'; img-src data:; style-src 'sha256-"))
        self.assertIn("base-uri 'none'; form-action 'none'", policy)
        self.assertNotIn("unsafe", policy)
        self.assertNotIn("script-src", policy)
        self.assertEqual(len(self.page.named("style")), 1)
        digest = base64.b64encode(hashlib.sha256("".join(self.page.styles).encode("utf-8")).digest()).decode("ascii")
        self.assertIn(f"style-src 'sha256-{digest}';", policy)
        names = [tag for tag, _ in self.page.tags]
        self.assertLess(names.index("meta"), names.index("style"))
        self.assertLess(self.document.index("Content-Security-Policy"), self.document.index("<style>"))

    def test_one_keyboard_reachable_control_switches_before_and_after(self):
        radios = self.page.named("input")
        self.assertEqual([(item["type"], item["name"], item["id"]) for item in radios],
                         [("radio", "view", "view-before"), ("radio", "view", "view-after")])
        self.assertIn("checked", radios[0])
        self.assertNotIn("checked", radios[1])
        for item in radios:
            self.assertNotIn("disabled", item)
            self.assertNotIn("tabindex", item)
            self.assertNotIn("hidden", item)
        self.assertEqual([item.get("for") for item in self.page.named("label")], ["view-before", "view-after"])
        self.assertEqual(len(self.page.named("div", role="radiogroup")), 1)
        self.assertTrue(self.page.named("div", role="radiogroup")[0]["aria-label"])
        css = "".join(self.page.styles)
        self.assertIn(".compare input{position:absolute;opacity:0;", css)
        self.assertIn(".compare input:checked+label{background:", css)
        self.assertIn(".compare input:focus-visible+label{outline:3px solid", css)
        self.assertIn(".state-after,.after{display:none}", css)
        self.assertIn("body:has(#view-after:checked) .after{display:inline}", css)
        self.assertIn("body:has(#view-after:checked) .state-after{display:block}", css)
        self.assertIn("body:has(#view-after:checked) .state-before{display:none}", css)
        self.assertIn("Showing the page as captured. The outlined area is where the change applies.", self.document)
        self.assertIn("Showing the proposed change: text color", self.document)
        self.assertEqual([item["filter"] for item in self.page.named("use", **{"class": "after"})], ["url(#recolor)"])

    def test_the_affected_region_is_outlined_on_the_real_capture(self):
        box = self.findings[0]["box"]
        marks = self.page.named("rect", **{"class": "mark"})
        self.assertEqual(len(marks), 1)
        self.assertAlmostEqual(float(marks[0]["x"]), box["x"] * 390 - 4, places=1)
        self.assertAlmostEqual(float(marks[0]["y"]), box["y"] * 844 - 4, places=1)
        self.assertAlmostEqual(float(marks[0]["width"]), box["width"] * 390 + 8, places=1)
        image = self.page.named("image")[0]
        self.assertEqual(image["href"], "data:image/png;base64," + self.clean["frames"][0]["screenshot"]["data"])
        shot = self.page.named("svg", **{"class": "shot"})[0]
        self.assertEqual((shot["viewbox"], shot["width"], shot["height"], shot["role"]), ("0 0 390 844", "390", "844", "img"))
        self.assertIn("“2 of 2 rooms” is hard to read", self.document)
        self.assertIn("<dt>Change</dt>", self.document)
        self.assertIn("<dt>Check</dt>", self.document)
        self.assertIn('<tr class="hit"><td>5</td><td>2 of 2 rooms<br>status</td>', self.document)
        self.assertIn("IBM Plex Sans<br>16 px, weight 400", self.document)
        self.assertIn("left 10%, top 52%, 50% × 5% of the view", self.document)

    def test_the_after_view_recolors_the_captured_text_pixels_and_leaves_the_fill_alone(self):
        plan = self.findings[0]["preview"]
        old, new = plan["from"], plan["to"]
        rows = preview.recolor_matrix(old, new, PAPER)

        def filtered(pixel):
            return [255 * (sum(rows[channel][index] * pixel[index] / 255 for index in range(3)) + rows[channel][4])
                    for channel in range(3)]

        for coverage in (0.0, 0.25, 0.5, 1.0):
            pixel = [PAPER[index] + coverage * (old[index] - PAPER[index]) for index in range(3)]
            expected = [PAPER[index] + coverage * (new[index] - PAPER[index]) for index in range(3)]
            for got, want in zip(filtered(pixel), expected):
                self.assertAlmostEqual(got, want, places=6)
        self.assertEqual(rows[3], [0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertIsNone(preview.recolor_matrix(PAPER, new, PAPER))
        swatch = preview.recolor_matrix([246, 245, 100], [246, 245, 0], PAPER)
        self.assertEqual([round(255 * (swatch[channel][2] * 100 / 255 + swatch[channel][4])) for channel in range(3)],
                         [246, 245, 0])
        matrix = self.page.named("fecolormatrix")[0]
        self.assertEqual(matrix["type"], "matrix")
        self.assertEqual(len(matrix["values"].split()), 20)
        recolor = self.page.named("filter", id="recolor")[0]
        self.assertEqual((recolor["filterunits"], recolor["color-interpolation-filters"]), ("userSpaceOnUse", "sRGB"))
        self.assertAlmostEqual(float(recolor["x"]), 39.0, places=1)
        self.assertAlmostEqual(float(recolor["width"]), 195.0, places=1)

    def test_hostile_page_text_is_shown_as_text_and_never_becomes_markup(self):
        bundle = board(title="</title><script>alert(1)</script>")
        hostile = bundle["frames"][0]["regions"][4]
        hostile["name"] = '"><img src=x onerror=alert(2)></style><script>alert(3)</script>'
        hostile["locator"] = "javascript:alert(4)"
        hostile["role"] = "<b>status"
        hostile["heading"] = "<iframe src=//evil.example>"
        clean = evidence.normalize(bundle)
        findings = checks.local_findings(clean)
        self.assertEqual(kinds(findings), ["contrast"])
        document = preview.build_preview(clean, findings)
        page = Page(document)
        self.assert_inert(document, page)
        self.assertNotIn("b", [tag for tag, _ in page.tags])
        self.assertEqual(len(page.named("style")), 1)
        self.assertIn("&lt;script&gt;alert(3)&lt;/script&gt;", document)
        self.assertIn("&lt;iframe src=//evil.example&gt;", document)
        self.assertNotIn("alert(4)", json.dumps(clean))

    def test_layout_findings_say_plainly_that_there_is_no_after_view(self):
        clean = evidence.normalize(wide_board())
        document = preview.build_preview(clean, checks.local_findings(clean))
        page = Page(document)
        self.assert_inert(document, page)
        self.assertEqual(page.named("input"), [])
        self.assertEqual(page.named("use", **{"class": "after"}), [])
        self.assertEqual(len(page.named("rect", **{"class": "mark"})), 1)
        self.assertIn("No after view for this change: it moves layout", document)
        self.assertIn("finding 1 of 2", document)

    def test_text_the_same_color_as_its_background_gets_a_finding_but_no_after_view(self):
        bundle = board()
        bundle["frames"][0]["regions"][4]["ink"] = [246, 245, 241, 1]
        clean = evidence.normalize(bundle)
        findings = checks.local_findings(clean)
        self.assertEqual(kinds(findings), ["contrast"])
        self.assertIn("measures 1.0 to 1", findings[0]["problem"])
        self.assertIsNone(preview.after_matrix(findings[0]))
        self.assertIsNotNone(preview.after_matrix(self.findings[0]))
        self.assertIsNone(preview.after_matrix(None))
        document = preview.build_preview(clean, findings)
        self.assertIn("No after view: the text and its background are the same color", document)
        self.assertEqual(Page(document).named("input"), [])

    def test_a_clean_view_gets_an_honest_message_and_no_compare_control(self):
        bundle = board()
        bundle["frames"][0]["regions"][4]["ink"] = [22, 24, 29, 1]
        clean = evidence.normalize(bundle)
        self.assertEqual(checks.local_findings(clean), [])
        document = preview.build_preview(clean, [])
        page = Page(document)
        self.assert_inert(document, page)
        self.assertIn("Local checks found nothing to fix in this view.", document)
        self.assertIn("needs a visual review, which this build does not run", document)
        self.assertEqual(page.named("input"), [])
        self.assertEqual(page.named("rect", **{"class": "mark"}), [])

    def test_the_preview_says_what_was_removed_and_that_nothing_was_uploaded(self):
        for sentence in ("Page address stored as https://boards.example/rooms?day=today.",
                         "Visual review by a model: not run. Nothing was uploaded.",
                         "This file has no scripts and loads nothing from the network."):
            self.assertIn(sentence, self.document)

    def test_the_preview_and_the_popup_pass_this_projects_own_checks(self):
        def rgb(value):
            return [int(value[index:index + 2], 16) for index in (1, 3, 5)]

        ink, muted, paper = (rgb(preview.PALETTE[name]) for name in ("ink", "muted", "paper"))
        self.assertGreaterEqual(checks.contrast_ratio(ink, paper), 4.5)
        self.assertGreaterEqual(checks.contrast_ratio(muted, paper), 4.5)
        self.assertEqual(inspect_design(self.document), [])
        self.assertEqual(inspect_design((EXTENSION / "popup.html").read_text(encoding="utf-8")), [])
        self.assertEqual(inspect_design((EXTENSION / "popup.css").read_text(encoding="utf-8")), [])


class PipelineTests(unittest.TestCase):
    def test_review_writes_a_private_preview_and_reports_each_stage_separately(self):
        with tempfile.TemporaryDirectory() as folder:
            result = review(board(), folder)
            self.assertTrue(result["ok"], result)
            saved = Path(result["preview_path"])
            self.assertEqual(saved.parent.parent, Path(folder))
            self.assertEqual(saved.parent.name, result["capture_id"])
            self.assertRegex(result["capture_id"], r"^c-[0-9a-f]{12}$")
            self.assertEqual(stat.S_IMODE(saved.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(saved.parent.stat().st_mode), 0o700)
            self.assertTrue(result["preview_url"].startswith("file:///"))
            self.assertIn("“2 of 2 rooms” is hard to read", saved.read_text(encoding="utf-8"))
            stored = json.loads((saved.parent / "evidence.json").read_text(encoding="utf-8"))
            self.assertNotIn("data", stored["frames"][0]["screenshot"])
            self.assertEqual(stored["frames"][0]["screenshot"]["sha256"], hashlib.sha256(png()).hexdigest())
            self.assertEqual(sorted(path.name for path in saved.parent.iterdir()), ["evidence.json", "preview.html"])
        self.assertEqual(result["critique"]["region"], "r5")
        self.assertEqual((result["has_after"], result["more_findings"], result["regions"]), (True, 0, 5))
        timings = result["timings_ms"]
        self.assertEqual((timings["page_load"], timings["capture"], timings["frontier"]), ("unknown", 212, "not-run"))
        for stage in ("sanitize", "local_checks", "preview"):
            self.assertGreaterEqual(timings[stage], 0)
        self.assertEqual(result["frontier"]["status"], "not-run")
        self.assertLess(len(json.dumps(result).encode("utf-8")), host.MAX_REPLY)
        lines = pipeline.describe(result)
        self.assertEqual(lines[0], result["critique"]["problem"])
        self.assertTrue(lines[1].startswith("Change: Change the text color"))
        self.assertTrue(lines[2].startswith("Check: “2 of 2 rooms” measures at least 4.5 to 1"))
        self.assertIn("Visual review by a model: not run. Nothing was uploaded.", lines)
        self.assertIn("page load unknown, capture 212 ms", lines[-1])

    def test_a_clean_view_reports_a_message_instead_of_an_invented_finding(self):
        bundle = board()
        bundle["frames"][0]["regions"][4]["ink"] = [22, 24, 29, 1]
        with tempfile.TemporaryDirectory() as folder:
            result = review(bundle, folder)
        self.assertEqual((result["ok"], result["critique"], result["has_after"]), (True, None, False))
        self.assertEqual(result["message"], pipeline.NO_FINDING)
        self.assertIn(pipeline.NO_FINDING, pipeline.describe(result))

    def test_only_the_newest_reviews_are_kept_and_other_files_are_left_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for index in range(4):
                old = root / f"c-{index:012x}"
                old.mkdir()
                (old / "preview.html").write_text("old", encoding="utf-8")
                os.utime(old, (index, index))
            (root / "notes").mkdir()
            (root / "notes" / "mine.txt").write_text("keep", encoding="utf-8")
            foreign = root / f"c-{9:012x}"
            foreign.mkdir()
            (foreign / "other.txt").write_text("keep", encoding="utf-8")
            os.utime(foreign, (0, 0))
            pipeline._prune(root, keep=2, protect="c-000000000000")
            self.assertEqual(sorted(path.name for path in root.iterdir()),
                             ["c-000000000000", "c-000000000002", "c-000000000003", "c-000000000009", "notes"])
            self.assertTrue((foreign / "other.txt").is_file())
            self.assertTrue((root / "notes" / "mine.txt").is_file())


class HostTests(unittest.TestCase):
    def serve(self, request, argv=None, root=None):
        stdout = io.BytesIO()
        with contextlib.redirect_stderr(io.StringIO()):
            status = host.main(["--allowed-origin", ORIGIN, ORIGIN] if argv is None else argv,
                               io.BytesIO(request), stdout, root)
        return status, stdout.getvalue()

    def test_only_the_one_pinned_extension_origin_is_served(self):
        other = "chrome-extension://" + "p" * 32 + "/"
        refused = (
            [],
            [ORIGIN],
            ["--allowed-origin", ORIGIN],
            ["--allowed-origin", ORIGIN, other],
            ["--allowed-origin", ORIGIN, ORIGIN.rstrip("/")],
            ["--allowed-origin", "chrome-extension://*/", "chrome-extension://*/"],
            ["--allowed-origin", ORIGIN + "\n", ORIGIN + "\n"],
            ["--allowed-origin", ORIGIN, "--parent-window=1", "https://evil.example/"],
        )
        for argv in refused:
            with self.subTest(argv=argv):
                self.assertEqual(self.serve(framed({"type": "ping"}), argv), (2, b""))
        status, out = self.serve(framed({"type": "ping"}), ["--allowed-origin", ORIGIN, ORIGIN, "--parent-window=7"])
        self.assertEqual(status, 0)
        self.assertEqual((unframed(out)["host"], unframed(out)["schema"]), ("com.design_mcp.review", SCHEMA))

    def test_oversized_empty_truncated_and_unreadable_frames_are_refused(self):
        cases = (
            (struct.pack("=I", host.MAX_REQUEST + 1) + b"{}", "frame-too-large"),
            (struct.pack("=I", 0), "frame-too-large"),
            (struct.pack("=I", 50) + b'{"type":', "truncated"),
            (b"\x01", "no-request"),
            (framed(["ping"]), "malformed"),
            (struct.pack("=I", 3) + b"\xff\xfe\xfd", "malformed"),
        )
        for request, code in cases:
            with self.subTest(code=code):
                status, out = self.serve(request)
                self.assertEqual((status, unframed(out)["code"]), (1, code))
        self.assertLessEqual(host.MAX_REPLY, 1024 * 1024)
        stream = io.BytesIO()
        host.write_frame(stream, {"ok": True, "blob": "x" * (host.MAX_REPLY + 1)})
        self.assertEqual(unframed(stream.getvalue())["code"], "reply-too-large")

    def test_a_capture_from_the_extension_returns_a_critique_and_a_preview_file(self):
        with tempfile.TemporaryDirectory() as folder:
            status, out = self.serve(framed({"type": "review", "bundle": board()}), root=folder)
            reply = unframed(out)
            self.assertEqual(status, 0)
            self.assertEqual((reply["critique"]["check"], reply["critique"]["region"]), ("contrast", "r5"))
            self.assertTrue(Path(reply["preview_path"]).is_file())
            self.assertLess(len(out), host.MAX_REPLY)
        status, out = self.serve(framed({"type": "review", "bundle": {"schema": SCHEMA}}), root="unused")
        self.assertEqual((status, unframed(out)["code"]), (1, "not-user-triggered"))
        status, out = self.serve(framed({"type": "export-everything"}), root="unused")
        self.assertEqual((status, unframed(out)["code"]), (1, "unknown-request"))
        self.assertFalse(Path("unused").exists())

    def test_install_pins_one_extension_and_writes_only_two_files(self):
        with tempfile.TemporaryDirectory() as home:
            plan = host.install(EXTENSION_ID, home=home, python="/opt/tools/design mcp/bin/python", platform="darwin")
            manifest = json.loads(plan["manifest_path"].read_text(encoding="utf-8"))
            self.assertEqual(manifest, {
                "name": "com.design_mcp.review",
                "description": "Design MCP local page review",
                "path": str(plan["launcher_path"]),
                "type": "stdio",
                "allowed_origins": [ORIGIN],
            })
            self.assertEqual(plan["manifest_path"], Path(home) / "Library" / "Application Support" / "Google"
                             / "Chrome" / "NativeMessagingHosts" / "com.design_mcp.review.json")
            launcher = plan["launcher_path"].read_text(encoding="utf-8")
            self.assertTrue(launcher.startswith("#!/bin/sh\n"))
            self.assertIn("exec '/opt/tools/design mcp/bin/python' -I -m design_mcp.review.host "
                          f'--allowed-origin {ORIGIN} "$@"\n', launcher)
            self.assertEqual(stat.S_IMODE(plan["launcher_path"].stat().st_mode), 0o700)
            self.assertEqual(len([path for path in Path(home).rglob("*") if path.is_file()]), 2)
            self.assertEqual(len(host.uninstall(home=home, platform="darwin")), 2)
            self.assertEqual([path for path in Path(home).rglob("*") if path.is_file()], [])
            self.assertEqual(host.uninstall(home=home, platform="darwin"), [])

    def test_custom_chrome_profiles_keep_their_native_hosts_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            home = Path(folder)
            first, second = home / "chrome-one", home / "chrome-two"
            first.mkdir()
            second.mkdir()
            first_plan = host.install(EXTENSION_ID, home=home, platform="linux", chrome_user_data_dir=first)
            second_id = "p" * 32
            second_plan = host.install(second_id, home=home, platform="linux", chrome_user_data_dir=second)
            self.assertEqual(first_plan["manifest_path"].parent, first / "NativeMessagingHosts")
            self.assertEqual(json.loads(first_plan["manifest_path"].read_text())["allowed_origins"], [ORIGIN])
            self.assertIn(second_id, second_plan["launcher_path"].read_text())
            self.assertNotEqual(first_plan["launcher_path"], second_plan["launcher_path"])
            self.assertEqual(len(host.uninstall(home=home, platform="linux", chrome_user_data_dir=first)), 2)
            self.assertTrue(second_plan["manifest_path"].is_file())
            self.assertTrue(second_plan["launcher_path"].is_file())
            with self.assertRaises(host.InstallError):
                host.plan_install(EXTENSION_ID, home=home, platform="linux", chrome_user_data_dir="relative")

    def test_install_refuses_anything_that_is_not_exactly_one_extension_id(self):
        for bad in ("", "*", "abc", EXTENSION_ID + "/", EXTENSION_ID + "\n", EXTENSION_ID.upper(),
                    "abcdefghijklmnoq" * 2, None):
            with self.subTest(bad=bad):
                with self.assertRaises(host.InstallError):
                    host.plan_install(bad, home="/nonexistent-home", platform="darwin")
        with self.assertRaises(host.InstallError):
            host.plan_install(EXTENSION_ID, home="/nonexistent-home", platform="win32")
        self.assertEqual(host.plan_install(EXTENSION_ID, home="/nonexistent-home", platform="linux")["manifest_path"],
                         Path("/nonexistent-home/.config/google-chrome/NativeMessagingHosts/com.design_mcp.review.json"))


class CliTests(unittest.TestCase):
    def run_cli(self, *argv):
        out, err, opened = io.StringIO(), io.StringIO(), []
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = cli.main(list(argv), opener=opened.append)
        return status, out.getvalue(), err.getvalue(), opened

    def test_review_is_wired_into_the_packaged_command(self):
        from design_mcp import cli as packaged

        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["design-mcp", "review", "--extension-path"]), contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit) as stopped:
                packaged.main()
        self.assertEqual(stopped.exception.code, 0)
        folder = Path(out.getvalue().splitlines()[0])
        self.assertEqual(folder.resolve(), EXTENSION.resolve())
        self.assertLessEqual({"collector.js", "manifest.json", "popup.css", "popup.html", "popup.js"},
                             {path.name for path in folder.iterdir()})

    def test_the_existing_commands_still_answer(self):
        from design_mcp import __version__, cli as packaged

        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["design-mcp", "version"]), contextlib.redirect_stdout(out):
            packaged.main()
        self.assertEqual(out.getvalue().strip(), f"design-mcp {__version__}")
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["design-mcp", "--help"]), contextlib.redirect_stdout(out):
            packaged.main()
        for line in ("design-mcp serve", "design-mcp version", "design-mcp review"):
            self.assertIn(line, out.getvalue())

    def test_a_saved_capture_becomes_a_critique_and_a_preview_file(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "capture.json"
            source.write_text(json.dumps(board()), encoding="utf-8")
            target = str(Path(folder) / "out")
            status, out, err, opened = self.run_cli("--evidence", str(source), "--out", target)
            self.assertEqual((status, err, opened), (0, "", []))
            lines = out.splitlines()
            self.assertTrue(lines[0].startswith("“2 of 2 rooms” is hard to read at 390 px wide"))
            self.assertTrue(lines[1].startswith("Change: "))
            self.assertTrue(lines[2].startswith("Check: "))
            saved = next(line for line in lines if line.startswith("Preview (before and after): "))
            self.assertTrue(Path(saved.split(": ", 1)[1]).is_file())
            status, out, _, _ = self.run_cli("--evidence", str(source), "--out", target, "--json")
            self.assertEqual((status, json.loads(out)["critique"]["region"]), (0, "r5"))
            status, _, err, _ = self.run_cli("--evidence", str(Path(folder) / "missing.json"))
            self.assertEqual(status, 1)
            self.assertIn("Could not read", err)

    def test_a_pasted_public_address_opens_for_a_scan_the_person_starts(self):
        status, out, err, opened = self.run_cli("boards.example/rooms#today")
        self.assertEqual((status, err, opened), (0, "", ["https://boards.example/rooms"]))
        self.assertIn("Opening https://boards.example/rooms in your browser.", out)
        self.assertIn("click the Design MCP button, then “Review this page”", out)
        status, out, _, opened = self.run_cli("https://boards.example/rooms", "--no-open")
        self.assertEqual((status, opened), (0, []))
        self.assertIn("Would open https://boards.example/rooms in your browser.", out)

    def test_addresses_that_are_not_public_pages_are_refused_with_the_reason(self):
        cases = (
            ("file:///etc/hosts", "Only http and https pages"),
            ("data:text/html,hi", "Only http and https pages"),
            ("javascript:alert(1)", "Only http and https pages"),
            ("https://chris:pw@boards.example/", "a sign-in name or password"),
            ("https://boards.example/?token=abc", "the value of “token”"),
            ("localhost:3000", "private network"),
            ("http://192.168.1.10/", "private network"),
        )
        for pasted, reason in cases:
            with self.subTest(pasted=pasted):
                status, out, err, opened = self.run_cli(pasted)
                self.assertEqual((status, out, opened), (1, "", []))
                self.assertIn(reason, err)

    @unittest.skipUnless(sys.platform == "darwin" or sys.platform.startswith("linux"), "host setup is macOS and Linux")
    def test_install_host_dry_run_shows_the_files_and_writes_nothing(self):
        with mock.patch.object(host, "install", side_effect=AssertionError("a dry run must not write")):
            status, out, err, _ = self.run_cli("--install-host", EXTENSION_ID, "--dry-run")
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(out.count("Would write "), 2)
        self.assertIn(f"Only {ORIGIN} can start the local reviewer.", out)
        status, out, err, _ = self.run_cli("--install-host", "not-an-id", "--dry-run")
        self.assertEqual((status, out), (1, ""))
        self.assertIn("32 letters from a to p", err)

    def test_no_arguments_prints_help_and_does_nothing(self):
        status, out, _, opened = self.run_cli()
        self.assertEqual((status, opened), (2, []))
        self.assertIn("design-mcp review", out)


class ExtensionTests(unittest.TestCase):
    def read(self, name):
        return (EXTENSION / name).read_text(encoding="utf-8")

    def test_the_extension_asks_only_for_the_active_tab_and_the_local_reviewer(self):
        manifest = json.loads(self.read("manifest.json"))
        self.assertEqual(manifest["manifest_version"], 3)
        self.assertEqual(sorted(manifest["permissions"]), ["activeTab", "nativeMessaging", "scripting"])
        for key in ("host_permissions", "optional_permissions", "optional_host_permissions", "content_scripts",
                    "background", "web_accessible_resources", "externally_connectable", "key", "update_url"):
            self.assertNotIn(key, manifest)
        policy = manifest["content_security_policy"]["extension_pages"]
        for part in ("default-src 'none'", "script-src 'self'", "style-src 'self'", "connect-src 'none'",
                     "form-action 'none'", "base-uri 'none'"):
            self.assertIn(part, policy)
        self.assertNotIn("unsafe", policy)
        self.assertNotIn("http", policy)
        self.assertEqual(manifest["action"], {"default_title": "Review this page", "default_popup": "popup.html"})
        self.assertEqual(manifest["incognito"], "not_allowed")

    def test_the_first_view_has_one_primary_action_and_loads_only_its_own_files(self):
        page = Page(self.read("popup.html"))
        primary = [attrs for tag, attrs, hidden in page.elements
                   if tag == "button" and "primary" in (attrs.get("class") or "").split() and not hidden]
        self.assertEqual([attrs["id"] for attrs in primary], ["scan"])
        self.assertIn("autofocus", primary[0])
        self.assertEqual([attrs.get("src") for attrs in page.named("script")], ["collector.js", "popup.js"])
        self.assertTrue(all("defer" in attrs for attrs in page.named("script")))
        self.assertEqual([attrs.get("href") for attrs in page.named("link")], ["popup.css"])
        self.assertEqual(page.named("img") + page.named("iframe") + page.named("style"), [])
        for tag, attrs in page.tags:
            self.assertFalse(any(name.startswith("on") or name == "style" for name in attrs), tag)
        self.assertEqual(len(page.named("p", role="status")), 1)
        for name in ("popup.html", "popup.css", "popup.js", "collector.js", "manifest.json"):
            self.assertIsNone(re.search(r"https?://[a-z0-9]", self.read(name), re.I), name)

    def test_nothing_is_requested_or_sent_before_the_person_presses_the_button(self):
        script = self.read("popup.js")
        for banned in ("fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "EventSource", "importScripts",
                       "innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            self.assertNotIn(banned, script)
        capture_start, render_start = script.index("async function capture()"), script.index("function render(")
        scan_start, paste_start = script.index("async function scan()"), script.index("function openPasted(")
        for call in ("chrome.tabs.query(", "chrome.scripting.executeScript(", "chrome.tabs.captureVisibleTab("):
            positions = [match.start() for match in re.finditer(re.escape(call), script)]
            self.assertTrue(positions and all(capture_start < position < render_start for position in positions), call)
        self.assertEqual(script.count("chrome.runtime.sendNativeMessage("), 1)
        self.assertTrue(scan_start < script.index("chrome.runtime.sendNativeMessage(") < paste_start)
        self.assertLess(script.index("await blankOut(picture"), script.index("frame.masks.applied = true"))
        self.assertTrue(script.rstrip().endswith("show('idle', IDLE_TEXT);"))
        self.assertIn(f"const SCHEMA = '{SCHEMA}';", script)
        self.assertIn(f"const HOST = '{host.HOST_NAME}';", script)
        self.assertIn("user_triggered: true", script)

    def test_the_collector_never_reads_typed_values_or_changes_the_page(self):
        source = self.read("collector.js")
        self.assertIsNone(re.search(r"\.value\b", source))
        self.assertEqual(source.count("getAttribute('value')"), 1)
        for banned in (".checked", ".selectedOptions", ".selectedIndex", ".files", "innerText", "innerHTML",
                       "outerHTML", "document.cookie", "localStorage", "sessionStorage", "indexedDB", "fetch(",
                       "XMLHttpRequest", "setAttribute(", "appendChild(", ".remove(", ".click(", ".focus(",
                       ".submit(", "dispatchEvent(", "scrollTo(", "scrollIntoView("):
            self.assertNotIn(banned, source)
        self.assertEqual(source.count("function designMcpCollect(options) {"), 1)
        for field in ("reading_order", "locator", "landmark", "heading", "size_px", "weight", "ink", "fill_flat",
                      "pressed", "scroll_width", "client_width", "covered_by", "has_text", "masked", "dpr"):
            self.assertIn(field, source)
        for kind in ("'frame'", "'field'", "'editable'"):
            self.assertIn(kind, source)
        expression = isolated.collect_expression()
        self.assertTrue(expression.startswith("(() => {"))
        self.assertTrue(expression.endswith("return designMcpCollect({maxRegions: 8});})()"))

    def test_the_separate_browser_receipts_are_parsed_strictly(self):
        self.assertEqual(isolated._marked("noise\nREVIEW_LOAD 412\n", "REVIEW_LOAD "), 412)
        self.assertEqual(isolated._marked('REVIEW_FRAME {"capture_ms": 9} trailing', "REVIEW_FRAME "), {"capture_ms": 9})
        with self.assertRaises(RuntimeError):
            isolated._marked("page said nothing", "REVIEW_FRAME ")
        self.assertEqual(isolated.VIEWPORTS, ((1440, 900), (390, 844)))

    def test_the_extension_ships_in_the_package_and_review_needs_no_third_party_code(self):
        with open(ROOT / "pyproject.toml", "rb") as stream:
            project = tomllib.load(stream)
        self.assertIn("review/extension/*", project["tool"]["setuptools"]["package-data"]["design_mcp"])
        self.assertEqual(project["project"]["scripts"], {"design-mcp": "design_mcp.cli:main"})
        probe = ("import sys, design_mcp.review.cli, design_mcp.review.host, design_mcp.review.isolated; "
                 "print(sorted(name for name in sys.modules "
                 "if name.split('.')[0] in ('fastmcp', 'pydantic', 'httpx', 'mcp')))")
        done = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=ROOT, timeout=60)
        self.assertEqual(done.stdout.strip(), "[]", done.stderr)


if __name__ == "__main__":
    unittest.main()
