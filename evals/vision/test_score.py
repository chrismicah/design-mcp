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
        self.observations = {
            "build_sha256": digest(b"candidate build"),
            "builder_session": "builder-1",
            "evaluator_session": "evaluator-2",
            "screens": {name: {
                "opened": "Local candidate, Review heading",
                "before_sha256": digest(f"initial {name}".encode()),
                "after_sha256": digest(name.encode()),
                "actions": [{"input": "Press Enter on Review", "expected": "Review opens",
                             "observed": "Findings heading appeared"}],
            } for name in self.screens},
        }
        self.evidence = json.dumps(self.observations).encode()
        self.browser = {
            "evidence_sha256": digest(self.evidence),
            "build_sha256": self.observations["build_sha256"],
            "checks": {key: True for key in HARD_GATES},
            "captures": {name: digest(name.encode()) for name in self.screens},
            "before_captures": {name: digest(f"initial {name}".encode()) for name in self.screens},
        }
        self.ballot = {"live_review_sha256": self.browser["evidence_sha256"],
                       "build_sha256": self.observations["build_sha256"],
                       "evaluator_session": self.observations["evaluator_session"],
                       "screens": [screen(name, self.browser["captures"][name]) for name in self.screens]}

    def evaluate_ballot(self):
        return evaluate(self.ballot, self.browser, self.screens, self.observations)

    def test_accepts_exact_threshold_on_both_screens(self):
        result = self.evaluate_ballot()
        self.assertTrue(result["accepted"])
        self.assertEqual(result["scores"], {"desktop": 9.5, "mobile": 9.5})

    def test_originality_and_coherence_outweigh_polished_controls(self):
        ratings = self.ballot["screens"][0]["ratings"]
        for key in ("coherence", "originality"):
            ratings[key]["score"] = 9
        for key in ("craft", "usability"):
            ratings[key]["score"] = 10
        result = self.evaluate_ballot()
        self.assertFalse(result["accepted"])
        self.assertEqual(result["scores"]["desktop"], 9.4)

    def test_independent_browser_failure_cannot_be_averaged_away(self):
        self.browser["checks"]["primary_action"] = False
        result = self.evaluate_ballot()
        self.assertFalse(result["accepted"])
        self.assertIn("primary_action", result["blockers"])

    def test_material_weakness_blocks_despite_high_ratings(self):
        self.ballot["screens"][1]["findings"].append({
            "severity": "material", "region": "filter row", "problem": "Small targets bunch together",
            "repair": "Align targets vertically", "expected_change": "Space separates the two targets",
        })
        self.assertFalse(self.evaluate_ballot()["accepted"])

    def test_requires_every_screen(self):
        self.ballot["screens"].pop()
        with self.assertRaisesRegex(ValueError, "required screen"):
            self.evaluate_ballot()

    def test_rejects_a_stale_ballot_for_the_same_screen_id(self):
        self.ballot["screens"][1]["capture_sha256"] = digest(b"older mobile")
        with self.assertRaisesRegex(ValueError, "different capture for mobile"):
            self.evaluate_ballot()

    def test_rejects_a_screenshot_only_ballot(self):
        del self.ballot["live_review_sha256"]
        with self.assertRaisesRegex(ValueError, "identify its live review evidence"):
            self.evaluate_ballot()

    def test_requires_actual_interaction_in_each_view(self):
        self.observations["screens"]["mobile"]["actions"] = []
        with self.assertRaisesRegex(ValueError, "interacting with the live design on mobile"):
            self.evaluate_ballot()

    def test_requires_observed_outcome(self):
        del self.observations["screens"]["mobile"]["actions"][0]["observed"]
        with self.assertRaisesRegex(ValueError, "observed result on mobile"):
            self.evaluate_ballot()

    def test_rejects_an_unstructured_observation_file(self):
        self.observations = "The screenshots look good"
        with self.assertRaisesRegex(ValueError, "cover each required screen"):
            self.evaluate_ballot()

    def test_rejects_a_different_build(self):
        self.ballot["build_sha256"] = digest(b"another candidate build")
        with self.assertRaisesRegex(ValueError, "same build"):
            self.evaluate_ballot()

    def test_rejects_builder_as_evaluator(self):
        self.observations["builder_session"] = self.observations["evaluator_session"]
        with self.assertRaisesRegex(ValueError, "independent evaluator session"):
            self.evaluate_ballot()

    def test_cli_verifies_capture_bytes_before_accepting(self):
        with TemporaryDirectory() as root:
            folder = Path(root)
            ballot = folder / "ballot.json"
            ballot.write_text(json.dumps(self.ballot))
            browser = folder / "browser.json"
            browser.write_text(json.dumps(self.browser))
            evidence = folder / "observations.json"
            evidence.write_bytes(self.evidence)
            command = [sys.executable, str(Path(__file__).with_name("score.py")),
                       "--ballot", str(ballot), "--browser", str(browser), "--browser-evidence", str(evidence)]
            for name in self.screens:
                path = folder / name
                path.write_bytes(name.encode())
                before = folder / f"{name}-before"
                before.write_bytes(f"initial {name}".encode())
                command.extend(["--screen", name, "--capture", name, str(path),
                                "--before-capture", name, str(before)])
            verified = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            (folder / "mobile").write_bytes(b"older mobile")
            stale = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("Capture file differs from the tested receipt for mobile", stale.stderr)
            (folder / "mobile").write_bytes(b"mobile")
            (folder / "mobile-before").write_bytes(b"initial desktop")
            duplicate = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("Before capture differs from the tested receipt for mobile", duplicate.stderr)


if __name__ == "__main__":
    unittest.main()
