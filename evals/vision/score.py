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


def evaluate(ballot, browser, expected_screens):
    screens = ballot["screens"]
    ids = [screen["id"] for screen in screens]
    expected = set(expected_screens)
    if not expected or len(expected) != len(expected_screens) or len(ids) != len(expected) or set(ids) != expected:
        raise ValueError("The ballot must include each required screen exactly once")
    if not is_digest(browser.get("evidence_sha256")):
        raise ValueError("A browser evidence hash is required")
    captures = browser.get("captures", {})
    if set(captures) != expected or not all(is_digest(value) for value in captures.values()):
        raise ValueError("The browser receipt must identify each required capture")
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
    args = parser.parse_args()
    browser = json.loads(args.browser.read_text())
    if hashlib.sha256(args.browser_evidence.read_bytes()).hexdigest() != browser.get("evidence_sha256"):
        parser.error("Browser evidence differs from the tested receipt")
    paths = dict(args.capture)
    if len(paths) != len(args.capture) or set(paths) != set(args.screen):
        parser.error("Pass exactly one capture file for each required screen")
    try:
        result = evaluate(json.loads(args.ballot.read_text()), browser, args.screen)
        for screen, path in paths.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != browser["captures"][screen]:
                raise ValueError(f"Capture file differs from the tested receipt for {screen}")
    except (KeyError, OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["accepted"] else 2)


if __name__ == "__main__":
    main()
