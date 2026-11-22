import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from score import HARD_GATES, WEIGHTS, evaluate


def digest(data):
    return hashlib.sha256(data).hexdigest()


def screen(name, capture_sha256, score=9.5):
    return {
        "id": name,
        "capture_sha256": capture_sha256,
        "ratings": {key: {"score": score, "evidence": "Visible reading order and action"} for key in WEIGHTS},
        "findings": [],
    }


class VisionGateTests(unittest.TestCase):
    def setUp(self):
        self.screens = ["desktop", "mobile"]
        self.browser = {
            "evidence_sha256": digest(b"browser evidence"),
            "checks": {key: True for key in HARD_GATES},
            "captures": {name: digest(name.encode()) for name in self.screens},
        }
        self.ballot = {"screens": [screen(name, self.browser["captures"][name]) for name in self.screens]}

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

    def test_rejects_a_stale_ballot_for_the_same_screen_id(self):
        self.ballot["screens"][1]["capture_sha256"] = digest(b"older mobile")
        with self.assertRaisesRegex(ValueError, "different capture for mobile"):
            evaluate(self.ballot, self.browser, self.screens)

    def test_cli_verifies_capture_bytes_before_accepting(self):
        with TemporaryDirectory() as root:
            folder = Path(root)
            ballot = folder / "ballot.json"
            ballot.write_text(json.dumps(self.ballot))
            browser = folder / "browser.json"
            browser.write_text(json.dumps(self.browser))
            evidence = folder / "observations.txt"
            evidence.write_bytes(b"browser evidence")
            command = [sys.executable, str(Path(__file__).with_name("score.py")),
                       "--ballot", str(ballot), "--browser", str(browser), "--browser-evidence", str(evidence)]
            for name in self.screens:
                path = folder / name
                path.write_bytes(name.encode())
                command.extend(["--screen", name, "--capture", name, str(path)])
            verified = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            (folder / "mobile").write_bytes(b"older mobile")
            stale = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("Capture file differs from the tested receipt for mobile", stale.stderr)


if __name__ == "__main__":
    unittest.main()
