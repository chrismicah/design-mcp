"""Report the strongest verified trial and require a second live release ballot."""

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evals.vision.score import MINIMUM, WEIGHTS, is_digest, session_key, weighted_score

RECEIPTS = ROOT / "evidence" / "benchmark-v1"
WIDTHS = (1440, 390)
ARMS = ("v2", "social")
MIN_ROUNDS = 5
MAX_ROUNDS = 15


def scores(ballot):
    pair = {}
    for screen, observation in ballot["screens"].items():
        width = int(screen.split("-")[1])
        key = (observation["arm"], width)
        if key in pair:
            raise ValueError("Duplicate arm and width in browser ballot")
        score = weighted_score({metric: observation.get(metric) for metric in WEIGHTS})
        reported = observation.get("weighted")
        if type(reported) not in (int, float) or reported != float(score):
            raise ValueError(f"Weighted score differs from the rubric on {screen}")
        pair[key] = {**observation, "verified_score": score}
    expected = {(arm, width) for arm in ARMS for width in WIDTHS}
    if (pair.keys() != expected or
            ballot["verified_screens"] != ballot["required_screens"] or
            ballot["verified_screens"] != len(expected)):
        raise ValueError("The ballot needs four verified views")
    return pair


def verify_builds(pair, generation):
    for (arm, _), observation in pair.items():
        if observation["html_sha256"] != generation[arm]["html_sha256"]:
            raise ValueError(f"Ballot does not review the recorded {arm} build")


def viewport_scores(pair, arm):
    return {width: pair[(arm, width)]["weighted"] for width in WIDTHS}


def capture_signature(pair, arm):
    return tuple(pair[arm, width][state]["sha256"]
                 for width in WIDTHS for state in ("before", "after"))


def gates(pair):
    return {
        "minimum_score_met": all(pair["social", width]["verified_score"] >= MINIMUM for width in WIDTHS),
        "beats_control_at_both_widths": all(pair["social", width]["verified_score"] > pair["v2", width]["verified_score"]
                                            for width in WIDTHS),
        "originality_improves_at_both_widths": all(
            pair[("social", width)]["originality"] > pair[("v2", width)]["originality"] for width in WIDTHS),
        "usability_preserved_at_both_widths": all(
            pair[("social", width)]["usability"] >= pair[("v2", width)]["usability"] for width in WIDTHS),
    }


def series_closed(rounds, misses):
    return rounds >= MAX_ROUNDS or (rounds >= MIN_ROUNDS and misses >= 2)


def record_live_session(ballot, critic_threads, critic_traces, browser_traces, error):
    reviewer = ballot.get("evaluator_thread")
    thread = session_key(reviewer) if isinstance(reviewer, str) else ""
    critic = ballot.get("trace_sha256")
    browser = ballot.get("browser_audit_sha256")
    if (not thread or thread in critic_threads or
            not is_digest(critic) or critic in critic_traces or not is_digest(browser) or browser in browser_traces):
        raise ValueError(error)
    critic_threads.add(thread)
    critic_traces.add(critic)
    browser_traces.add(browser)


def result(case, receipts=RECEIPTS, confirmation=None):
    candidates = []
    for path in receipts.glob(f"social-{case}-live-r*.json"):
        receipt = json.loads(path.read_text(encoding="utf-8"))
        candidates.append(receipt)
    candidates.sort(key=lambda receipt: receipt["source"]["round"])
    if not candidates:
        raise ValueError(f"No audit receipts for {case}")
    strongest = None
    series = {}
    series_name = None
    series_best = None
    misses = 0
    critic_threads = set()
    critic_traces = set()
    browser_traces = set()
    candidate_hashes = set()
    candidate_captures = set()
    control_hash = candidates[0]["generation"]["v2"]["html_sha256"]
    for expected_round, receipt in enumerate(candidates, start=1):
        if (receipt["source"]["round"] != expected_round or
                receipt["ballot"]["case"] != f"social-{case}" or
                receipt["generation"]["v2"]["html_sha256"] != control_hash):
            raise ValueError("Expected consecutive rounds with the same archived control")
        ballot = receipt["ballot"]
        record_live_session(ballot, critic_threads, critic_traces, browser_traces,
                            "Each round requires a fresh critic session and distinct live traces")
        pair = scores(ballot)
        verify_builds(pair, receipt["generation"])
        candidate_hash = receipt["generation"]["social"]["html_sha256"]
        if candidate_hash == control_hash or candidate_hash in candidate_hashes:
            raise ValueError("Each round requires a distinct candidate build")
        candidate_hashes.add(candidate_hash)
        signature = capture_signature(pair, "social")
        if signature == capture_signature(pair, "v2") or signature in candidate_captures:
            raise ValueError("Identical live captures cannot count as a new creative round")
        candidate_captures.add(signature)
        values = [pair["social", width]["verified_score"] for width in WIDTHS]
        rank = (min(values), sum(values) / len(values))
        if strongest is None or rank > strongest["rank"]:
            strongest = {"round": expected_round, "rank": rank, "receipt": receipt, "pair": pair}
        name = receipt["source"].get("series", "original")
        if name != series_name:
            if name in series:
                raise ValueError("A closed series cannot be resumed under its original identity")
            series[name] = 0
            series_name = name
            series_best = None
        elif series_closed(series[name], misses):
            raise ValueError("This series is closed. Try a distinct design premise in a new series.")
        series[name] += 1
        if series_best is None or rank > series_best:
            series_best = rank
            misses = 0
        else:
            misses += 1
    best = strongest["pair"]
    primary_gates = gates(best)
    confirmation_report = None
    if confirmation is None:
        archived = receipts / f"social-{case}-confirmation-r{strongest['round']}.json"
        if archived.is_file():
            confirmation = json.loads(archived.read_text(encoding="utf-8"))
    if confirmation is not None:
        primary = strongest["receipt"]["ballot"]
        error = "Confirmation requires a separate audited live session on this case"
        if confirmation["case"] != primary["case"]:
            raise ValueError(error)
        record_live_session(confirmation, critic_threads, critic_traces, browser_traces, error)
        second = scores(confirmation)
        verify_builds(second, strongest["receipt"]["generation"])
        confirmation_report = {
            "scores": viewport_scores(second, "social"),
            "paired_control": viewport_scores(second, "v2"),
            **gates(second),
        }
    active_rounds = series[series_name]
    minimum_rounds_met = len(candidates) >= MIN_ROUNDS
    closed = series_closed(active_rounds, misses)
    next_round = "new premise" if closed else "pivot" if misses else "refine"
    return {
        "scored_rounds": len(candidates),
        "minimum_rounds_met": minimum_rounds_met,
        "best_round": strongest["round"],
        "best": viewport_scores(best, "social"),
        "paired_control": viewport_scores(best, "v2"),
        **primary_gates,
        "confirmation": confirmation_report,
        "confirmed_score_gate": (
            minimum_rounds_met and all(primary_gates.values()) and confirmation_report is not None and
            all(confirmation_report[key] for key in primary_gates)
        ),
        "current_series": series_name,
        "rounds_in_current_series": active_rounds,
        "consecutive_rounds_without_improvement": misses,
        "series_stopping_rule_met": closed,
        "next_round": next_round,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for case in ("lighting", "river"):
        parser.add_argument(f"--{case}-confirmation", type=Path, help="Independent audited.json for the strongest round")
    args = parser.parse_args()
    results = {}
    for case in ("lighting", "river"):
        path = getattr(args, f"{case}_confirmation")
        confirmation = json.loads(path.read_text(encoding="utf-8")) if path else None
        results[case] = result(case, confirmation=confirmation)
    print(json.dumps(results, indent=2))
