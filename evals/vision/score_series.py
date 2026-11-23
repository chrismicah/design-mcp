"""Verify a creative website's live critique history and finalist confirmation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from score import session_key, verify_files


SCREENS = ("desktop", "mobile")


def verify_packet(packet, root):
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

    result = verify_files(
        pinned_file("ballot"),
        pinned_file("browser"),
        local_file(packet["observations"]),
        SCREENS,
        {name: local_file(path) for name, path in packet["before"].items()},
        {name: local_file(path) for name, path in packet["after"].items()},
    )
    if sha256(local_file(packet["build"]).read_bytes()).hexdigest() != result["build_sha256"]:
        raise ValueError("The archived build differs from the reviewed build digest")
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
    evaluators = set()
    for number, entry in enumerate(rounds, 1):
        fields = ["premise", "critique"]
        if number > 1:
            fields.append("revision")
        for field in fields:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Round {number} needs a concrete {field}")
        result = verify_packet(entry["review"], root)
        if result["build_sha256"] in builds:
            raise ValueError(f"Round {number} repeats a previously reviewed build")
        if result["capture_set"] in captures:
            raise ValueError(f"Round {number} reuses the same before and after captures")
        evaluator = session_key(result["evaluator_session"])
        if evaluator in evaluators:
            raise ValueError(f"Round {number} needs a fresh evaluator session")
        builds.add(result["build_sha256"])
        captures.add(result["capture_set"])
        evaluators.add(evaluator)
        history.append({"round": number, **result})

    chosen = history[finalist - 1]
    confirmation = verify_packet(series["confirmation"], root)
    if any(confirmation[field] != chosen[field] for field in ("build_sha256", "builder_session")):
        raise ValueError("Confirm the same finalist build and builder")
    participants = {session_key(row[role]) for row in history for role in ("builder_session", "evaluator_session")}
    if session_key(confirmation["evaluator_session"]) in participants:
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
