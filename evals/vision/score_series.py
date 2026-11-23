"""Verify a creative website's live critique history and finalist confirmation."""

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from score import session_key, verify_files


SCREENS = ("desktop", "mobile")


def finalist_rank(result):
    scores = [Decimal(str(result["scores"][screen])) for screen in SCREENS]
    return result["eligible_for_finalist"], min(scores), sum(scores)


def verify_packet(packet, root, *, assertion=None, expected_outcome=None):
    def local_file(value):
        relative = Path(value)
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            raise ValueError("Review files must be inside the series directory")
        return path

    def pinned_file(field):
        path = local_file(packet[field])
        if sha256(path.read_bytes()).hexdigest() != packet[f"{field}_sha256"]:
            raise ValueError(f"The {field} file differs from its frozen digest")
        return path

    observations = local_file(packet["observations"])
    result = verify_files(
        pinned_file("ballot"),
        pinned_file("browser"),
        observations,
        SCREENS,
        {name: local_file(path) for name, path in packet["before"].items()},
        {name: local_file(path) for name, path in packet["after"].items()},
    )
    if sha256(local_file(packet["build"]).read_bytes()).hexdigest() != result["build_sha256"]:
        raise ValueError("The archived build differs from the reviewed build digest")
    if assertion is not None:
        screens = json.loads(observations.read_bytes())["screens"]
        for name in SCREENS:
            matches = [action for action in screens[name]["actions"] if action["expected"] == assertion]
            if len(matches) != 1 or matches[0].get("passed") is not expected_outcome:
                raise ValueError(f"Pivot assertion must {'pass' if expected_outcome else 'fail'} on {name}")
    return result


def evaluate_series(series, root):
    root = root.resolve()
    rounds = series["rounds"]
    if not isinstance(rounds, list) or not 5 <= len(rounds) <= 15:
        raise ValueError("Record 5–15 live revision rounds")
    finalist = series["finalist_round"]
    if type(finalist) is not int or not 1 <= finalist <= len(rounds):
        raise ValueError("Identify the finalist by its round number, starting at 1")

    history = []
    builds = set()
    captures = set()
    builders = set()
    evaluators = set()
    best_rank = None
    stalled_rounds = 0
    for number, entry in enumerate(rounds, 1):
        fields = ["premise", "critique"]
        if number > 1:
            fields.append("revision")
        for field in fields:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Round {number} needs a concrete {field}")
        pivot = entry.get("pivot")
        if number > 5 and stalled_rounds >= 2:
            raise ValueError(f"Round {number} exceeds the stop rule after two non-improving rounds")
        if stalled_rounds >= 2 and pivot is None:
            raise ValueError(f"Round {number} needs a tested pivot after two non-improving rounds")
        if pivot is None:
            result = verify_packet(entry["review"], root)
        else:
            if not history:
                raise ValueError("A pivot needs a previously reviewed control")
            assertion = pivot["assertion"]
            if not isinstance(assertion, str) or not assertion.strip():
                raise ValueError(f"Round {number} needs a testable pivot assertion")
            control = verify_packet(pivot["control"], root, assertion=assertion, expected_outcome=False)
            result = verify_packet(entry["review"], root, assertion=assertion, expected_outcome=True)
            parent = history[-1]
            if any(control[field] != parent[field] for field in ("build_sha256", "builder_session")):
                raise ValueError("Test the pivot against the exact previous build and builder")
            if control["evaluator_session"] != result["evaluator_session"]:
                raise ValueError("The same independent evaluator must test both sides of the pivot")
            if control["capture_set"] in captures or control["capture_set"] == result["capture_set"]:
                raise ValueError("A pivot needs fresh control and candidate captures")
            captures.add(control["capture_set"])
            stalled_rounds = 0
        if result["build_sha256"] in builds:
            raise ValueError(f"Round {number} repeats a previously reviewed build")
        if result["capture_set"] in captures:
            raise ValueError(f"Round {number} reuses the same before and after captures")
        builder = session_key(result["builder_session"])
        evaluator = session_key(result["evaluator_session"])
        if evaluator in evaluators:
            raise ValueError(f"Round {number} needs a fresh evaluator session")
        if evaluator in builders or builder in evaluators:
            raise ValueError(f"Round {number} mixes builder and evaluator roles in the series")
        builds.add(result["build_sha256"])
        captures.add(result["capture_set"])
        builders.add(builder)
        evaluators.add(evaluator)
        history.append({"round": number, **result})
        rank = finalist_rank(result)
        if best_rank is None or rank > best_rank:
            best_rank = rank
            stalled_rounds = 0
        else:
            stalled_rounds += 1

    chosen = history[finalist - 1]
    if finalist_rank(chosen) != best_rank:
        strongest = next(entry["round"] for entry in history if finalist_rank(entry) == best_rank)
        raise ValueError(f"Round {strongest} ranks higher than the selected finalist")
    confirmation = verify_packet(series["confirmation"], root)
    if any(confirmation[field] != chosen[field] for field in ("build_sha256", "builder_session")):
        raise ValueError("Confirm the same finalist build and builder")
    if session_key(confirmation["evaluator_session"]) in builders | evaluators:
        raise ValueError("Confirmation needs a fresh evaluator outside the review history")

    return {"accepted": chosen["accepted"] and confirmation["accepted"],
            "finalist_round": finalist, "rounds": history, "confirmation": confirmation}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        series = json.loads(args.manifest.read_text())
        result = evaluate_series(series, args.manifest.parent)
    except (AttributeError, KeyError, OSError, TypeError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["accepted"] else 2)


if __name__ == "__main__":
    main()
