"""Check when cached browser evidence can answer the theatre filter question."""

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROOMS = ("Hall A", "Studio B")  # The locator order in the archived Playwriter replay.
WIDTHS = ("1440", "390")


def read(path):
    return json.loads(path.read_bytes())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def remaining_room(view):
    """Return a room only when matched locators, control state, and counts agree."""
    before, filtered, restored = (view.get(state) for state in ("before", "filtered", "restored"))
    if before != [1, 1, "2 of 2 rooms"] or restored != [1, 1, "2 of 2 rooms", "true"]:
        return None
    if not isinstance(filtered, list) or len(filtered) != 4:
        return None
    counts = filtered[:2]
    if any(type(count) is not int or count not in (0, 1) for count in counts):
        return None
    if sum(counts) != 1 or filtered[2:] != ["1 of 2 rooms", "true"]:
        return None
    return ROOMS[counts.index(1)]


def replay(bench):
    evidence = ROOT / "evidence/benchmark-v1"
    source = bench / "remote-captures/44984687051/dashboard-venue/v2"
    smoke = bench / "computer-smoke/interaction-v2"
    receipt = read(smoke / "receipt.json")
    archived = read(evidence / "preflight.json")["first_generation_playwriter_interaction"]
    vision = read(evidence / "vision-packet-ablation.json")
    if receipt != archived or set(receipt["widths"]) != set(WIDTHS):
        raise ValueError("Unexpected Playwriter interaction receipt")
    if sha256(source / "index.html") != receipt["input_sha256"] or receipt["input_sha256"] != vision["fixture_sha256"]:
        raise ValueError("The interaction and original visual ballot must use the same HTML")

    images = [source / f"{width}.png" for width in WIDTHS]
    images += [smoke / f"delayed-{width}.png" for width in WIDTHS]
    hashes = [sha256(image) for image in images]
    if hashes != vision["packet_image_hashes"]["full"]:
        raise ValueError("The four original visual inputs must match the full-packet ballot")

    views = receipt["widths"]
    ballot = vision["results"]["full"]["ballot"]
    answers = {width: remaining_room(views[width]) for width in WIDTHS}
    expected = {"1440": ballot["desktop_room_after_filter"], "390": ballot["mobile_room_after_filter"]}
    if answers != expected or any(room is None for room in answers.values()):
        raise ValueError("Local evidence does not reproduce the full-packet filter answer")

    negative = {}
    for width, view in views.items():
        if view["screenshot_sha256"] != sha256(smoke / f"delayed-{width}.png"):
            raise ValueError(f"Filtered screenshot does not match the interaction at {width}")
        missing = deepcopy(view)
        del missing["filtered"]
        inconsistent = deepcopy(view)
        inconsistent["filtered"][2] = "2 of 2 rooms"
        unpressed = deepcopy(view)
        unpressed["filtered"][3] = "false"
        failures = {"missing_state": missing, "status_mismatch": inconsistent, "unpressed": unpressed}
        negative[width] = {name: remaining_room(state) is None for name, state in failures.items()}
        if not all(negative[width].values()):
            raise ValueError(f"Local review answered despite inconclusive evidence at {width}")

    return {
        "scope": "Deterministic replay of one synthetic theatre fixture and its archived GPT-6.2 Astra ballot.",
        "fixture_sha256": receipt["input_sha256"],
        "browser_replay_source_sha256": sha256(smoke.parent / "playwriter-smoke.py"),
        "browser_replay_locator_order": list(ROOMS),
        "full_packet_sha256": hashes,
        "local_answers": answers,
        "full_ballot_answers": expected,
        "frontier_calls_for_filter": 0,
        "frontier_input_tokens_for_filter": 0,
        "negative_controls_abstained": negative,
        "hierarchy": {
            "route": "full-frontier-packet",
            "archived_region": ballot["hierarchy_region"],
            "archived_problem": ballot["hierarchy_problem"],
            "archived_combined_packet_input_tokens": vision["results"]["full"]["usage"]["input_tokens"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bench", type=Path, help="Workspace directory with the frozen captures and interaction receipt")
    args = parser.parse_args()
    print(json.dumps(replay(args.bench), indent=2))


if __name__ == "__main__":
    main()
