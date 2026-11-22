import unittest

from score import HARD_GATES, WEIGHTS, evaluate


def screen(name, score=9.5):
    return {"id": name, "ratings": {key: {"score": score, "evidence": "Visible reading order and action"}
                                    for key in WEIGHTS}, "findings": []}


class VisionGateTests(unittest.TestCase):
    def setUp(self):
        self.browser = {"evidence_sha256": "a" * 64, "checks": {key: True for key in HARD_GATES}}
        self.screens = ["desktop", "mobile"]
        self.ballot = {"screens": [screen(name) for name in self.screens]}

    def test_accepts_exact_threshold_on_both_screens(self):
        result = evaluate(self.ballot, self.browser, self.screens)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["scores"], {"desktop": 9.5, "mobile": 9.5})

    def test_originality_and_coherence_outweigh_polished_controls(self):
        ratings = self.ballot["screens"][0]["ratings"]
        for key in ("coherence", "originality"):
            ratings[key]["score"] = 9
        for key in ("craft", "usability"):
            ratings[key]["score"] = 10
        result = evaluate(self.ballot, self.browser, self.screens)
        self.assertFalse(result["accepted"])
        self.assertEqual(result["scores"]["desktop"], 9.4)

    def test_independent_browser_failure_cannot_be_averaged_away(self):
        self.browser["checks"]["primary_action"] = False
        result = evaluate(self.ballot, self.browser, self.screens)
        self.assertFalse(result["accepted"])
        self.assertIn("primary_action", result["blockers"])

    def test_material_weakness_blocks_despite_high_ratings(self):
        self.ballot["screens"][1]["findings"].append({
            "severity": "material", "region": "filter row", "problem": "Small targets bunch together",
            "repair": "Align targets vertically", "expected_change": "Space separates the two targets",
        })
        self.assertFalse(evaluate(self.ballot, self.browser, self.screens)["accepted"])

    def test_requires_every_screen(self):
        self.ballot["screens"].pop()
        with self.assertRaisesRegex(ValueError, "required screen"):
            evaluate(self.ballot, self.browser, self.screens)


if __name__ == "__main__":
    unittest.main()
