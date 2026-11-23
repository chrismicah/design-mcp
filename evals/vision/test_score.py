import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from score import HARD_GATES, WEIGHTS, evaluate
from score_series import evaluate_series


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
        self.observations["builder_session"] = self.observations["evaluator_session"].upper() + " "
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


class CreativeSeriesTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.series = {
            "finalist_round": 4,
            "rounds": [{"premise": "The transcript marks the seam between two editions",
                        "critique": "The source time is easy to mistake for the broadcast time",
                        "revision": "Move the active edition name beside its clock",
                        "review": self.review(f"round-{number}", number, f"critic-{number}",
                                              rating)}
                       for number, rating in enumerate((8, 8.5, 9, 9.5, 8), 1)],
            "confirmation": self.review("final", 4, "fresh-critic", 9.5),
        }

    def review(self, label, build, critic, rating, capture_label=None, pivot_passed=None, *,
               builder="builder", primary_action=True):
        folder = self.folder / label
        folder.mkdir()
        before, after, observations = {}, {}, {}
        for name in ("desktop", "mobile"):
            changes = {}
            for stage, files in (("before", before), ("after", after)):
                path = folder / f"{name}-{stage}.png"
                content = f"{capture_label or label} {name} {stage}".encode()
                path.write_bytes(content)
                files[name] = str(path.relative_to(self.folder))
                changes[f"{stage}_sha256"] = digest(content)
            actions = [{"input": "Open source", "expected": "Interview time", "observed": "14:28"}]
            if pivot_passed is not None:
                passed = pivot_passed if isinstance(pivot_passed, bool) else pivot_passed[name]
                actions.append({"input": "Select the omitted words", "expected": "Selection switches the citation clock",
                                "observed": "14:28" if passed else "Clock stayed at 01:06", "passed": passed})
            observations[name] = {**changes, "opened": "Transcript", "actions": actions}

        build_bytes = f"<main>Candidate {build}</main>".encode()
        (folder / "index.html").write_bytes(build_bytes)
        build_sha = digest(build_bytes)
        evidence = json.dumps({"build_sha256": build_sha, "builder_session": builder,
                               "evaluator_session": critic, "screens": observations}).encode()
        (folder / "observations.json").write_bytes(evidence)
        captures = {name: data["after_sha256"] for name, data in observations.items()}
        browser = {"build_sha256": build_sha, "evidence_sha256": digest(evidence),
                   "checks": dict.fromkeys(HARD_GATES, True), "captures": captures,
                   "before_captures": {name: data["before_sha256"] for name, data in observations.items()}}
        browser["checks"]["primary_action"] = primary_action
        ballot = {"build_sha256": build_sha, "live_review_sha256": digest(evidence),
                  "evaluator_session": critic, "screens": [screen(name, capture,
                                                         rating[name] if isinstance(rating, dict) else rating)
                                                         for name, capture in captures.items()]}
        (folder / "browser.json").write_text(json.dumps(browser))
        (folder / "ballot.json").write_text(json.dumps(ballot))
        return {"build": f"{label}/index.html", "ballot": f"{label}/ballot.json", "browser": f"{label}/browser.json",
                "ballot_sha256": digest((folder / "ballot.json").read_bytes()),
                "browser_sha256": digest((folder / "browser.json").read_bytes()),
                "observations": f"{label}/observations.json", "before": before, "after": after}

    def test_retains_failed_rounds_and_passes_the_frozen_finalist(self):
        result = evaluate_series(self.series, self.folder)
        self.assertTrue(result["accepted"])
        self.assertEqual([row["accepted"] for row in result["rounds"]], [False, False, False, True, False])

    def test_finalist_prefers_the_higher_mean_when_the_weaker_screen_ties(self):
        self.series["rounds"][4]["review"] = self.review(
            "stronger-round", 5, "critic-5", {"desktop": 9.8, "mobile": 9.5})
        with self.assertRaisesRegex(ValueError, "Round 5 ranks higher"):
            evaluate_series(self.series, self.folder)

    def test_finalist_keeps_a_working_build_over_a_higher_scoring_broken_one(self):
        self.series["rounds"][4]["review"] = self.review(
            "broken-round", 5, "critic-5", 10, primary_action=False)
        self.assertTrue(evaluate_series(self.series, self.folder)["accepted"])

    def test_two_misses_at_round_five_end_the_series(self):
        self.series["rounds"][3]["review"] = self.review("miss-4", 4, "critic-4", 8)
        self.series["rounds"].append({
            **self.series["rounds"][4],
            "review": self.review("extra-round", 6, "critic-6", 10),
        })
        with self.assertRaisesRegex(ValueError, "Round 6 exceeds the stop rule"):
            evaluate_series(self.series, self.folder)

    def test_a_pivot_below_the_best_score_still_counts_as_a_miss(self):
        self.series["finalist_round"] = 3
        self.series["confirmation"] = self.review("confirmed-round-3", 3, "fresh-critic", 9)
        self.series["rounds"][3] = {
            **self.series["rounds"][3],
            "review": self.review("round-4-pivot", 4, "critic-4", 8.5, pivot_passed=True),
            "pivot": {
                "assertion": "Selection switches the citation clock",
                "control": self.review("round-4-pivot-control", 3, "critic-4", 9, pivot_passed=False),
            },
        }
        self.assertEqual(len(evaluate_series(self.series, self.folder)["rounds"]), 5)
        self.series["rounds"].append({
            **self.series["rounds"][4],
            "review": self.review("round-6", 6, "critic-6", 10),
        })
        with self.assertRaisesRegex(ValueError, "Round 6 exceeds the stop rule"):
            evaluate_series(self.series, self.folder)

    def test_short_history_cannot_release(self):
        self.series["rounds"].pop()
        with self.assertRaisesRegex(ValueError, "5–15 live revision rounds"):
            evaluate_series(self.series, self.folder)

    def test_requires_an_observable_revision(self):
        del self.series["rounds"][1]["revision"]
        with self.assertRaisesRegex(ValueError, "Round 2 needs a concrete revision"):
            evaluate_series(self.series, self.folder)

    def test_duplicate_build_cannot_count_as_a_real_revision(self):
        self.series["rounds"][1]["review"] = self.series["rounds"][0]["review"]
        with self.assertRaisesRegex(ValueError, "repeats a previously reviewed build"):
            evaluate_series(self.series, self.folder)

    def test_confirmation_requires_a_different_evaluator(self):
        self.series["confirmation"] = self.review("old-critic", 4, " CRITIC-4 ", 9.5)
        with self.assertRaisesRegex(ValueError, "fresh evaluator"):
            evaluate_series(self.series, self.folder)

    def test_confirmation_requires_the_same_build(self):
        self.series["confirmation"] = self.review("wrong-build", 8, "fresh-critic", 10)
        with self.assertRaisesRegex(ValueError, "same finalist build"):
            evaluate_series(self.series, self.folder)

    def test_confirmation_below_threshold_rejects_release(self):
        self.series["confirmation"] = self.review("below-threshold", 4, "fresh-critic", 9.49)
        self.assertFalse(evaluate_series(self.series, self.folder)["accepted"])

    def test_rewritten_ballot_cannot_replace_the_prior_result(self):
        (self.folder / "round-1/ballot.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "frozen digest"):
            evaluate_series(self.series, self.folder)

    def test_confirmation_cannot_claim_a_different_archived_build(self):
        (self.folder / "final/index.html").write_text("<main>Something else</main>")
        with self.assertRaisesRegex(ValueError, "archived build differs"):
            evaluate_series(self.series, self.folder)

    def test_requires_relative_evidence_paths(self):
        self.series["confirmation"]["build"] = str(self.folder / "final/index.html")
        with self.assertRaisesRegex(ValueError, "inside the series directory"):
            evaluate_series(self.series, self.folder)

    def test_rejects_duplicate_captures_for_a_new_build(self):
        self.series["rounds"][1]["review"] = self.review("same-captures", 2, "critic-2", 8, "round-1")
        with self.assertRaisesRegex(ValueError, "reuses the same before and after captures"):
            evaluate_series(self.series, self.folder)

    def test_each_round_needs_a_fresh_critic(self):
        self.series["rounds"][1]["review"] = self.review("same-critic", 2, "critic-1", 8)
        with self.assertRaisesRegex(ValueError, "needs a fresh evaluator"):
            evaluate_series(self.series, self.folder)

    def test_builder_and_critic_must_stay_separate_across_rounds(self):
        for builder, critic in (("second-builder", " Builder "), (" CRITIC-1 ", "second-critic")):
            with self.subTest(builder=builder, critic=critic):
                self.series["rounds"][1]["review"] = self.review(
                    f"mixed-role-{critic.strip()}", 2, critic, 8.5, builder=builder)
                with self.assertRaisesRegex(ValueError, "mixes builder and evaluator roles"):
                    evaluate_series(self.series, self.folder)

    def prepare_stalled_rounds(self):
        for number in (2, 3):
            self.series["rounds"][number - 1]["review"] = self.review(
                f"stalled-{number}", number, f"critic-{number}", 8)

    def prepare_pivot(self, *, parent=3, control_critic="critic-4", control_outcome=False, candidate_outcome=True):
        self.prepare_stalled_rounds()
        entry = self.series["rounds"][3]
        entry["review"] = self.review("pivot-candidate", 4, "critic-4", 9.5, pivot_passed=candidate_outcome)
        entry["pivot"] = {"assertion": "Selection switches the citation clock",
                          "control": self.review("pivot-control", parent, control_critic, 8,
                                                 pivot_passed=control_outcome)}

    def test_two_stalled_rounds_require_a_pivot_to_continue(self):
        self.prepare_stalled_rounds()
        with self.assertRaisesRegex(ValueError, "Round 4 needs a tested pivot"):
            evaluate_series(self.series, self.folder)

    def test_paired_pivot_can_continue_a_stalled_series(self):
        self.prepare_pivot()
        self.assertTrue(evaluate_series(self.series, self.folder)["accepted"])

    def test_cosmetic_revision_cannot_claim_a_pivot_when_both_builds_pass(self):
        self.prepare_pivot(control_outcome=True)
        with self.assertRaisesRegex(ValueError, "Pivot assertion must fail"):
            evaluate_series(self.series, self.folder)

    def test_pivot_must_work_on_phone(self):
        self.prepare_pivot(candidate_outcome={"desktop": True, "mobile": False})
        with self.assertRaisesRegex(ValueError, "Pivot assertion must pass on mobile"):
            evaluate_series(self.series, self.folder)

    def test_pivot_compares_the_exact_previous_build(self):
        self.prepare_pivot(parent=2)
        with self.assertRaisesRegex(ValueError, "exact previous build"):
            evaluate_series(self.series, self.folder)

    def test_pivot_uses_the_same_independent_evaluator(self):
        self.prepare_pivot(control_critic="another-critic")
        with self.assertRaisesRegex(ValueError, "same independent evaluator"):
            evaluate_series(self.series, self.folder)


if __name__ == "__main__":
    unittest.main()
