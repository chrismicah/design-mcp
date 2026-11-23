import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from status import RECEIPTS, result


class ConfirmationTest(unittest.TestCase):
    def setUp(self):
        self.primary = json.loads((RECEIPTS / "social-river-live-r5.json").read_text(encoding="utf-8"))
        self.primary["source"]["round"] = 1
        for view in self.primary["ballot"]["screens"].values():
            if view["arm"] == "social":
                view["weighted"] = 9.5
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.receipts = Path(folder.name)
        (self.receipts / "social-river-live-r1.json").write_text(json.dumps(self.primary), encoding="utf-8")
        self.second = copy.deepcopy(self.primary["ballot"])
        self.second.update(evaluator_thread="fresh", trace_sha256="new-trace", browser_audit_sha256="new-visit")

    def add_round(self, number, score=9.3, *, build=None, series=None, same_captures=False):
        receipt = copy.deepcopy(self.primary)
        receipt["source"]["round"] = number
        if series is not None:
            receipt["source"]["series"] = series
        receipt["ballot"]["evaluator_thread"] = f"critic-{number}"
        candidate = build or f"candidate-{number}"
        receipt["generation"]["social"]["html_sha256"] = candidate
        for label, view in receipt["ballot"]["screens"].items():
            if view["arm"] == "social":
                view["weighted"] = score
                view["html_sha256"] = candidate
                if not same_captures:
                    for state in ("before", "after"):
                        frame = f"{number}-{label}-{state}"
                        view[state]["sha256"] = hashlib.sha256(frame.encode()).hexdigest()
        path = self.receipts / f"social-river-live-r{number}.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")

    def test_confirmation_cannot_average_away_a_lower_mobile_score(self):
        self.assertFalse(result("river", self.receipts)["confirmed_score_gate"])
        for number in range(2, 5):
            self.add_round(number)
        self.assertFalse(result("river", self.receipts, self.second)["confirmed_score_gate"])
        self.add_round(5)
        self.assertTrue(result("river", self.receipts, self.second)["confirmed_score_gate"])
        for key, view in self.second["screens"].items():
            if view["arm"] == "social" and key.endswith("-390"):
                view["weighted"] = 9.49
        self.assertFalse(result("river", self.receipts, self.second)["confirmed_score_gate"])

    def test_rejects_reused_critic_or_different_build(self):
        with self.assertRaisesRegex(ValueError, "separate audited live session"):
            result("river", self.receipts, self.primary["ballot"])
        next(iter(self.second["screens"].values()))["html_sha256"] = "different-build"
        with self.assertRaisesRegex(ValueError, "recorded .* build"):
            result("river", self.receipts, self.second)

    def test_a_pivot_keeps_the_previous_best(self):
        self.add_round(2, series="floodwall")
        report = result("river", self.receipts)
        self.assertEqual(report["best_round"], 1)
        self.assertEqual(report["current_series"], "floodwall")
        self.assertEqual(report["consecutive_rounds_without_improvement"], 0)

    def test_rejects_a_duplicate_build_even_with_a_fresh_critic(self):
        self.add_round(2, build=self.primary["generation"]["social"]["html_sha256"])
        with self.assertRaisesRegex(ValueError, "distinct candidate"):
            result("river", self.receipts)

    def test_rejects_new_html_with_four_identical_captures(self):
        self.add_round(2, same_captures=True)
        with self.assertRaisesRegex(ValueError, "Identical live captures"):
            result("river", self.receipts)

    def test_a_stalled_series_requires_a_new_premise(self):
        self.add_round(2)
        self.assertEqual(result("river", self.receipts)["next_round"], "pivot")
        for number in range(3, 6):
            self.add_round(number)
        self.assertEqual(result("river", self.receipts)["next_round"], "new premise")
        self.add_round(6)
        with self.assertRaisesRegex(ValueError, "series is closed"):
            result("river", self.receipts)
        self.add_round(6, series="floodwall")
        self.assertEqual(result("river", self.receipts)["next_round"], "refine")
