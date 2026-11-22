"""Verify and export the frozen baseline's completed paired ballots without model calls."""

import argparse
import json
from pathlib import Path
import statistics
from types import SimpleNamespace

from generate import BASE_DIR, read_trace, sha256
from judge import WIDTHS, create_pair, load, run_judge, score_arm, summarize, write


ARMS = ("none", "v2")


def matching_run(archives, case, cells):
    matches = []
    for archive in archives.iterdir():
        if not archive.is_dir() or not archive.name.isdecimal():
            continue
        if all(
            (archive / case / arm / name).is_file()
            and (archive / case / arm / name).read_bytes() == (cells / case / arm / name).read_bytes()
            for arm in ARMS for name in ("receipt.json", "render.json")
        ):
            matches.append(archive)
    if len(matches) != 1:
        raise ValueError(f"Expected one matching capture archive for {case}, found {len(matches)}")
    return matches[0]


def verify_case(args, task):
    case = task["id"]
    pair = create_pair(args, task)
    if pair is None:
        raise ValueError(f"Ballot has no complete rendering for {case}")
    ballot = run_judge(args, task, pair, None)
    blind, labels, _ = pair
    if ballot["scores"] != {arm: score_arm(ballot["verdict"][label]) for label, arm in labels.items()}:
        raise ValueError(f"Ballot arithmetic does not match its ratings for {case}")
    trace = read_trace(args.out / "traces" / f"{case}.jsonl")
    turn = next((event for event in reversed(trace) if event["type"] == "turn.completed"), {})
    items = [event["item"] for event in trace if event["type"] == "item.completed"]
    message = next((item["text"] for item in reversed(items) if item["type"] == "agent_message"), "{}")
    if (not turn.get("usage") or turn["usage"] != ballot["usage"]
            or json.loads(message) != ballot["verdict"]):
        raise ValueError(f"Saved ballot differs from the judge trace for {case}")
    archive = matching_run(args.archives, case, args.cells)
    cells = {}
    for label, arm in labels.items():
        cell = args.cells / case / arm
        generation, render = load(cell / "receipt.json"), load(cell / "render.json")
        trace = args.generation / case / arm / "client.jsonl"
        if not generation["usage"] or sha256(trace.read_bytes()) != generation["trace_sha256"]:
            raise ValueError(f"Missing or changed generation trace for {case}/{arm}")
        captures = {}
        for width in WIDTHS:
            capture = render["captures"][width]
            archived = archive / case / arm / f"{width}.png"
            blind_image = blind / f"{label}-{width}.png"
            if (capture["viewport"] != int(width) or sha256(archived.read_bytes()) != capture["sha256"]
                    or sha256(blind_image.read_bytes()) != capture["sha256"]):
                raise ValueError(f"Capture identity differs for {case}/{arm}/{width}")
            captures[width] = {key: capture[key] for key in ("sha256", "viewport", "width", "pageErrors")}
        cells[arm] = {"generation": generation, "browser": render["browser"], "renderer": render["renderer"],
                      "captures": captures}
    return {"render_run": f"https://github.com/chrismicah/design-mcp/actions/runs/{archive.name}",
            "cells": cells, "ballot": ballot}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cells", "generation", "ballots", "archives", "report"):
        parser.add_argument(f"--{flag}", required=True, type=Path)
    paths = parser.parse_args()
    args = SimpleNamespace(cells=paths.cells, generation=paths.generation, out=paths.ballots, archives=paths.archives,
                           seed="design-mcp-blind-v1", control="none", treatment="v2",
                           compact=False, model="gpt-6.2-astra", effort="max")
    tasks = load(BASE_DIR / "tasks.json")
    cases = {task["id"]: verify_case(args, task) for task in tasks
             if (args.out / "ratings" / f"{task['id']}.json").is_file()}
    if not cases:
        parser.error("No completed baseline ballots were found")
    summary = summarize(tasks, [case["ballot"] for case in cases.values()])
    summary["median_usage"] = {
        arm: {
            **{field: statistics.median(case["cells"][arm]["generation"]["usage"][field] for case in cases.values())
               for field in ("input_tokens", "cached_input_tokens", "output_tokens")},
            "elapsed_seconds": statistics.median(case["cells"][arm]["generation"]["elapsed_seconds"]
                                                 for case in cases.values()),
        }
        for arm in ARMS
    }
    write(paths.report, {"summary": summary, "cases": cases})


if __name__ == "__main__":
    main()
