"""Verify and export completed paired ballots without model calls."""

import argparse
import json
from pathlib import Path
import statistics
from types import SimpleNamespace

from generate import BASE_DIR, read_trace, sha256
from judge import DEFAULT_BLIND_SEED, WIDTHS, create_pair, load, run_judge, score_arm, summarize, write


ARMS = ("none", "v2")


def archive_matches(archive, case, cells, arms):
    return archive.is_dir() and archive.name.isdecimal() and all(
        (archive / case / arm / name).is_file()
        and (archive / case / arm / name).read_bytes() == (cells / case / arm / name).read_bytes()
        for arm in arms for name in ("receipt.json", "render.json")
    )


def matching_run(archives, case, cells, arms=ARMS):
    matches = []
    for archive in archives.iterdir():
        if archive_matches(archive, case, cells, arms):
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
    arms = (args.control, args.treatment)
    if args.archives:
        archive = matching_run(args.archives, case, args.cells, arms)
        archives = dict.fromkeys(arms, archive)
    else:
        archives = {args.control: args.control_archive, args.treatment: args.treatment_archive}
        for arm, archive in archives.items():
            if not archive_matches(archive, case, args.cells, (arm,)):
                raise ValueError(f"Selected capture archive disagrees for {case}/{arm}")
    cells = {}
    for label, arm in labels.items():
        cell = args.cells / case / arm
        generation, render = load(cell / "receipt.json"), load(cell / "render.json")
        origin = (args.control_generation or args.generation) if arm == args.control else args.generation
        trace = origin / case / arm / "client.jsonl"
        if not generation["usage"] or sha256(trace.read_bytes()) != generation["trace_sha256"]:
            raise ValueError(f"Missing or changed generation trace for {case}/{arm}")
        archived_cell = archives[arm] / case / arm
        if sha256((archived_cell / "index.html").read_bytes()) != generation["html_sha256"]:
            raise ValueError(f"Archived HTML differs for {case}/{arm}")
        captures = {}
        for width in WIDTHS:
            capture = render["captures"][width]
            archived = archived_cell / f"{width}.png"
            blind_image = blind / f"{label}-{width}.png"
            if (capture["viewport"] != int(width) or sha256(archived.read_bytes()) != capture["sha256"]
                    or sha256(blind_image.read_bytes()) != capture["sha256"]):
                raise ValueError(f"Capture identity differs for {case}/{arm}/{width}")
            captures[width] = {key: capture[key] for key in ("sha256", "viewport", "width", "pageErrors")}
        cells[arm] = {"generation": generation, "browser": render["browser"], "renderer": render["renderer"],
                      "captures": captures}
    urls = {arm: f"https://github.com/chrismicah/design-mcp/actions/runs/{archive.name}"
            for arm, archive in archives.items()}
    runs = {"render_run": urls[args.control]} if len(set(urls.values())) == 1 else {"render_runs": urls}
    return {**runs, "cells": cells, "ballot": ballot}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cells", "generation", "ballots", "report"):
        parser.add_argument(f"--{flag}", required=True, type=Path)
    for flag in ("archives", "control-archive", "treatment-archive", "control-generation"):
        parser.add_argument(f"--{flag}", type=Path)
    parser.add_argument("--control", default=ARMS[0])
    parser.add_argument("--treatment", default=ARMS[1])
    parser.add_argument("--seed", default=DEFAULT_BLIND_SEED, help="The blinding seed used by judge.py")
    paths = parser.parse_args()
    if paths.control == paths.treatment:
        parser.error("Pass distinct names for the control and treatment")
    if paths.archives and (paths.control_archive or paths.treatment_archive):
        parser.error("Use either --archives or separate control and treatment archives")
    if not paths.archives and not (paths.control_archive and paths.treatment_archive):
        parser.error("Pass --archives or both --control-archive and --treatment-archive")
    args = SimpleNamespace(**vars(paths), out=paths.ballots,
                           compact=False, model="gpt-6.2-astra", effort="max")
    tasks = load(BASE_DIR / "tasks.json")
    cases = {task["id"]: verify_case(args, task) for task in tasks
             if (args.out / "ratings" / f"{task['id']}.json").is_file()}
    if not cases:
        parser.error("No completed paired ballots were found")
    summary = summarize(tasks, [case["ballot"] for case in cases.values()], args.treatment, args.control)
    summary["median_usage"] = {
        arm: {
            **{field: statistics.median(case["cells"][arm]["generation"]["usage"][field] for case in cases.values())
               for field in ("input_tokens", "cached_input_tokens", "output_tokens")},
            "elapsed_seconds": statistics.median(case["cells"][arm]["generation"]["elapsed_seconds"]
                                                 for case in cases.values()),
        }
        for arm in (args.control, args.treatment)
    }
    write(paths.report, {"summary": summary, "cases": cases})


if __name__ == "__main__":
    main()
