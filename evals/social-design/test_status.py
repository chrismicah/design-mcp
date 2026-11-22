import copy
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

    def test_confirmation_cannot_average_away_a_lower_mobile_score(self):
        self.assertFalse(result("river", self.receipts)["confirmed_score_gate"])
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
        revision = copy.deepcopy(self.primary)
        revision["source"].update(round=2, series="floodwall")
        revision["ballot"]["evaluator_thread"] = "pivot"
        for view in revision["ballot"]["screens"].values():
            if view["arm"] == "social":
                view["weighted"] = 9.3
        (self.receipts / "social-river-live-r2.json").write_text(json.dumps(revision), encoding="utf-8")

        report = result("river", self.receipts)
        self.assertEqual(report["best_round"], 1)
        self.assertEqual(report["current_series"], "floodwall")
        self.assertEqual(report["consecutive_rounds_without_improvement"], 0)
