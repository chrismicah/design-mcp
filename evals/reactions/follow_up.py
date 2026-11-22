"""Resume a sealed pilot arm with its next exact reaction after a live visual miss."""

import argparse
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace
from uuid import UUID

from pilot import HERE, PACKAGE_COMMIT, PILOT_CASES, generate

TOOLS = {"direct", "react", "check"}


def next_reaction(previous, ballot, case_id, arm):
    spec = json.loads((HERE / "tasks.json").read_bytes())
    case = next(item for item in spec["cases"] if item["source_case"] == case_id.split("-")[0])
    round_number = previous.get("reaction_number", 0)
    if type(round_number) is not int or not 0 <= round_number < min(2, len(case["reactions"])):
        raise ValueError("No sealed reaction remains for this draft")
    if (previous["case"], previous["arm"], previous["status"]) != (case_id, arm, "passed"):
        raise ValueError("Previous draft is ineligible")
    source = PACKAGE_COMMIT if arm == "design-mcp" else None
    if previous["source_commit"] != source or not previous["usage"]:
        raise ValueError("The previous draft does not match the pinned pilot arm")
    if (ballot["case"] != case_id or ballot["verified_screens"] != 4
            or ballot["required_screens"] != 4
            or set(ballot["screens"]) != {f"{label}-{width}" for label in ("A", "B") for width in (1440, 390)}):
        raise ValueError("An audited four-view ballot is required")
    screens = {label.rsplit("-", 1)[-1]: entry for label, entry in ballot["screens"].items()
               if entry["arm"] == arm and entry["html_sha256"] == previous["html_sha256"]}
    if set(screens) != {"1440", "390"}:
        raise ValueError("Both ballot views must match this draft")
    scores = [view["weighted"] for view in screens.values()]
    if not all(type(score) in (int, float) and 0 <= score <= 10 for score in scores):
        raise ValueError("The ballot must have valid weighted scores")
    if min(scores) >= 9.5:
        raise ValueError("This arm already reached the visual floor")
    return round_number + 1, case["reactions"][round_number]


def run(args):
    previous = json.loads((args.previous / "receipt.json").read_bytes())
    ballot = json.loads(args.ballot.read_bytes())
    round_number, reaction = next_reaction(previous, ballot, args.case, args.arm)
    for filename, field in (("index.html", "html_sha256"), ("client.jsonl", "trace_sha256"),
                            ("prompt.txt", "prompt_sha256")):
        if generate.sha256((args.previous / filename).read_bytes()) != previous[field]:
            raise ValueError(f"Previous draft hash mismatch: {filename}")
    thread_id = str(UUID(previous["thread_id"]))
    kit = args.kit.resolve()
    if json.loads((kit / "kit.json").read_bytes())["source_commit"] != PACKAGE_COMMIT:
        raise ValueError("Use the verified install kit for the sealed package")
    config = "mcp_servers={}"
    if args.arm == "design-mcp":
        server = (kit / "bin/design-mcp").resolve(strict=True)
        if not server.is_relative_to(kit / "tools/design-mcp"):
            raise ValueError("Design MCP executable is outside the verified install kit")
        config = generate.mcp_table(server, "design-mcp", ["serve"], {
            "DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false",
        })
    options = SimpleNamespace(codex=args.codex, model=previous["model"], effort=previous["effort"], no_shell=True)
    command = generate.client_command(options, config)
    command.remove("--ephemeral")
    command[-1:] = ["resume", thread_id, "-"]
    env = generate.clean_env()
    version = subprocess.check_output([args.codex, "--version"], env=env, text=True).strip()
    if version != previous["client"]:
        raise ValueError(f"Expected {previous['client']}, got {version}")

    out = args.out.resolve()
    out.mkdir(parents=True)
    generate.check_quota(args.quota_probe.resolve(), out)
    (out / "prompt.txt").write_bytes(reaction.encode())
    trace = out / "client.jsonl"
    start = time.monotonic()
    exit_code = None
    with trace.open("w") as stdout, (out / "client.stderr").open("w") as stderr:
        try:
            exit_code = subprocess.run(command, input=reaction, stdout=stdout, stderr=stderr, text=True,
                                       cwd=args.scratch.resolve(), env=env, timeout=900).returncode
        except subprocess.TimeoutExpired:
            pass
    events = generate.read_trace(trace)
    treatment = args.arm == "design-mcp"
    receipt, html = generate.parse_cell(events, treatment, expected_tool=TOOLS)
    calls = receipt["tool_calls"]
    if treatment and not calls and html and receipt["usage"] and not receipt["client_errors"]:
        receipt["status"] = "passed"
    if treatment and any(call["server"] != "design-mcp" or call["tool"] not in TOOLS for call in calls):
        receipt["status"] = "unpermitted-tool-call"
    observed = [event["thread_id"] for event in events if event.get("type") == "thread.started"]
    if exit_code is None:
        receipt["status"] = "timeout"
    elif exit_code:
        receipt["status"] = "client-error"
    elif observed != [thread_id]:
        receipt["status"] = "wrong-thread"
    if html:
        (out / "index.html").write_bytes(html.encode())
        receipt["html_sha256"] = generate.sha256(html.encode())
    receipt.update(case=args.case, arm=args.arm, thread_id=thread_id, client=version,
                   model=options.model, effort=options.effort, source_commit=previous["source_commit"],
                   reaction_number=round_number, previous_html_sha256=previous["html_sha256"],
                   elapsed_seconds=round(time.monotonic() - start, 2), exit_code=exit_code,
                   prompt_sha256=generate.sha256(reaction.encode()), trace_sha256=generate.sha256(trace.read_bytes()))
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple("-".join(case) for case in PILOT_CASES), required=True)
    parser.add_argument("--arm", choices=("plain", "design-mcp"), required=True)
    for option in ("previous", "ballot", "out", "kit", "quota-probe", "scratch"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    args = parser.parse_args()
    receipt = run(args)
    print(json.dumps(receipt))
    raise SystemExit(0 if receipt["status"] == "passed" else 2)


if __name__ == "__main__":
    main()
