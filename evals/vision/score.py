"""Apply the frozen visual release rubric to a blind ballot and browser receipt."""

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re


WEIGHTS = {
    "coherence": Decimal("0.30"),
    "originality": Decimal("0.30"),
    "craft": Decimal("0.20"),
    "usability": Decimal("0.20"),
}
MINIMUM = Decimal("9.5")
HARD_GATES = ("primary_action", "responsive_geometry", "privacy", "speed")
SHA256 = re.compile(r"[a-f0-9]{64}")


def is_digest(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def screen_score(screen):
    ratings = screen["ratings"]
    if set(ratings) != set(WEIGHTS):
        raise ValueError("Each screen needs exactly the four rubric ratings")
    score = Decimal(0)
    for name, weight in WEIGHTS.items():
        rating = ratings[name]
        value = rating["score"]
        evidence = rating["evidence"]
        if type(value) not in (int, float) or not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"Missing score or grounded evidence for {name}")
        amount = Decimal(str(value))
        if not amount.is_finite() or not Decimal(0) <= amount <= Decimal(10):
            raise ValueError(f"Score for {name} is outside 0–10")
        score += amount * weight
    return score


def verify_live_review(ballot, browser, observations, expected):
    if ballot.get("live_review_sha256") != browser["evidence_sha256"]:
        raise ValueError("The ballot must identify its live review evidence")
    if not isinstance(observations, dict):
        raise ValueError("Live review evidence must cover each required screen")
    build = browser.get("build_sha256")
    if not is_digest(build) or build != ballot.get("build_sha256") or build != observations.get("build_sha256"):
        raise ValueError("Browser, ballot and observations must cover the same build")
    reviewer = observations.get("evaluator_session")
    builder = observations.get("builder_session")
    if not all(isinstance(session, str) and session.strip() for session in (reviewer, builder)):
        raise ValueError("Identify the builder and evaluator sessions")
    if reviewer == builder or reviewer != ballot.get("evaluator_session"):
        raise ValueError("The ballot must come from the independent evaluator session")
    screens = observations.get("screens")
    if not isinstance(screens, dict) or set(screens) != expected:
        raise ValueError("Live review evidence must cover each required screen")
    before = browser.get("before_captures", {})
    if not isinstance(before, dict) or set(before) != expected or not all(is_digest(value) for value in before.values()):
        raise ValueError("The browser receipt must identify each before capture")
    for name, screen in screens.items():
        if not isinstance(screen, dict):
            raise ValueError(f"Invalid live review record for {name}")
        if screen.get("before_sha256") != before[name] or screen.get("after_sha256") != browser["captures"][name]:
            raise ValueError(f"Live review used different captures for {name}")
        opened = screen.get("opened")
        actions = screen.get("actions", [])
        if not isinstance(opened, str) or not opened.strip() or not isinstance(actions, list) or not actions:
            raise ValueError(f"Record opening and interacting with the live design on {name}")
        for action in actions:
            if not isinstance(action, dict) or not all(
                isinstance(action.get(field), str) and action[field].strip()
                for field in ("input", "expected", "observed")
            ):
                raise ValueError(f"Record the input, expected result and observed result on {name}")


def evaluate(ballot, browser, expected_screens, observations):
    screens = ballot["screens"]
    ids = [screen["id"] for screen in screens]
    expected = set(expected_screens)
    if not expected or len(expected) != len(expected_screens) or len(ids) != len(expected) or set(ids) != expected:
        raise ValueError("The ballot must include each required screen exactly once")
    if not is_digest(browser.get("evidence_sha256")):
        raise ValueError("A browser evidence hash is required")
    captures = browser.get("captures", {})
    if not isinstance(captures, dict) or set(captures) != expected or not all(is_digest(value) for value in captures.values()):
        raise ValueError("The browser receipt must identify each required capture")
    verify_live_review(ballot, browser, observations, expected)
    for screen in screens:
        if screen.get("capture_sha256") != captures[screen["id"]]:
            raise ValueError(f"The ballot reviewed a different capture for {screen['id']}")

    blockers = [name for name in HARD_GATES if browser["checks"].get(name) is not True]
    scores = {}
    for screen in screens:
        name = screen["id"]
        scores[name] = screen_score(screen)
        for finding in screen["findings"]:
            if finding["severity"] not in {"material", "minor"}:
                raise ValueError(f"Invalid finding severity on {name}")
            if not all(isinstance(finding.get(field), str) and finding[field].strip()
                       for field in ("region", "problem", "repair", "expected_change")):
                raise ValueError(f"Incomplete finding on {name}")
            if finding["severity"] == "material":
                blockers.append(f"{name}: {finding['region']}")
        if scores[name] < MINIMUM:
            blockers.append(f"{name}: below {MINIMUM}")

    return {"accepted": not blockers, "scores": {name: float(score) for name, score in scores.items()},
            "minimum": float(MINIMUM), "blockers": blockers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ballot", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--browser-evidence", type=Path, required=True)
    parser.add_argument("--screen", action="append", required=True)
    parser.add_argument("--capture", action="append", nargs=2, metavar=("SCREEN", "FILE"), required=True)
    parser.add_argument("--before-capture", action="append", nargs=2, metavar=("SCREEN", "FILE"), required=True)
    args = parser.parse_args()
    paths = dict(args.capture)
    before_paths = dict(args.before_capture)
    if len(paths) != len(args.capture) or set(paths) != set(args.screen):
        parser.error("Pass exactly one capture file for each required screen")
    if len(before_paths) != len(args.before_capture) or set(before_paths) != set(args.screen):
        parser.error("Pass exactly one before capture file for each required screen")
    try:
        browser = json.loads(args.browser.read_text())
        evidence = args.browser_evidence.read_bytes()
        if hashlib.sha256(evidence).hexdigest() != browser.get("evidence_sha256"):
            raise ValueError("Browser evidence differs from the tested receipt")
        result = evaluate(json.loads(args.ballot.read_text()), browser, args.screen, json.loads(evidence))
        for screen, path in paths.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != browser["captures"][screen]:
                raise ValueError(f"Capture file differs from the tested receipt for {screen}")
            if hashlib.sha256(Path(before_paths[screen]).read_bytes()).hexdigest() != browser["before_captures"][screen]:
                raise ValueError(f"Before capture differs from the tested receipt for {screen}")
    except (KeyError, OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["accepted"] else 2)


if __name__ == "__main__":
    main()
