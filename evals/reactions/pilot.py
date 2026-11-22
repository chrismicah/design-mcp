"""Run the four initial drafts in the sealed simulated non-designer pilot."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import random
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "v1"))
import generate

PILOT_CASES = (("dashboard", "clear"), ("pricing", "misleading"))
PACKAGE_COMMIT = "2fcd31221671590152401d958b904141e438e453"


def pilot_cases():
    spec = json.loads((HERE / "tasks.json").read_bytes())
    source = (ROOT / spec["project_context"]).read_bytes()
    if generate.sha256(source) != spec["project_context_sha256"]:
        raise ValueError("The sealed project context hash does not match")
    briefs = {row["id"]: row["brief"] for row in json.loads(source)}
    cases = {row["source_case"]: row for row in spec["cases"]}
    for name, variant in PILOT_CASES:
        _, separator, project = briefs[name].partition(". ")
        if not separator or not project:
            raise ValueError(f"Could not separate the project context for {name}")
        brief = f"Project context:\n{project}\n\nUser prompt:\n{cases[name]['prompts'][variant]}"
        yield f"{name}-{variant}", brief


def initial_prompt(brief):
    task = (
        "If you need a decision before you can build the UI, ask for it in a question-only "
        "reply and state your recommended option when you have one.\n\n"
    )
    return task + generate.PROMPT.format(brief=brief)


def run_draft(args, case, brief, arm, client_version):
    cell = args.out / case / arm
    cell.mkdir(parents=True)
    config = "mcp_servers={}"
    if arm == "design-mcp":
        config = generate.mcp_table(args.server, "design-mcp", ["serve"], {
            "DESIGN_MCP_SURFACE": "v2",
            "FASTMCP_SHOW_SERVER_BANNER": "false",
        })
    prompt = initial_prompt(brief)
    (cell / "prompt.txt").write_text(prompt, encoding="utf-8")
    trace_path = cell / "client.jsonl"
    command = generate.client_command(args, config)
    # Retain each independent session so its own first draft can receive a sealed reaction.
    command.remove("--ephemeral")
    (cell / "client-command.json").write_text(json.dumps(command, indent=2) + "\n")
    start = time.monotonic()
    exit_code = None
    with trace_path.open("w", encoding="utf-8") as stdout, (cell / "client.stderr").open("w") as stderr:
        try:
            exit_code = subprocess.run(
                command, input=prompt, text=True, stdout=stdout, stderr=stderr,
                env=generate.clean_env(), cwd=args.scratch, timeout=args.timeout,
            ).returncode
        except subprocess.TimeoutExpired:
            pass

    events = generate.read_trace(trace_path)
    receipt, html = generate.parse_cell(events, expect_mcp=arm == "design-mcp")
    messages = [
        event["item"]["text"]
        for event in events
        if event.get("type") == "item.completed" and event["item"].get("type") == "agent_message"
    ]
    if messages:
        (cell / "reply.txt").write_text(messages[-1], encoding="utf-8")
    if exit_code is None:
        receipt["status"] = "timeout"
    elif exit_code:
        receipt["status"] = "client-error"
    elif not html and messages and receipt["status"] in {"invalid-html", "mcp-unused-or-failed"} and not receipt["client_errors"]:
        receipt["status"] = "review-reply"
    elif html:
        (cell / "index.html").write_bytes(html.encode())
        receipt["html_sha256"] = generate.sha256(html.encode())
    receipt.update(
        case=case, arm=arm, source_commit=PACKAGE_COMMIT if arm == "design-mcp" else None,
        model=args.model, effort=args.effort, client=client_version, exit_code=exit_code,
        elapsed_seconds=round(time.monotonic() - start, 2),
        prompt_sha256=generate.sha256(prompt.encode()),
        trace_sha256=generate.sha256(trace_path.read_bytes()),
        thread_id=next((event["thread_id"] for event in events if event.get("type") == "thread.started"), None),
    )
    (cell / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in ("case", "arm", "status", "elapsed_seconds", "usage")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--kit", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--quota-probe", required=True, type=lambda value: Path(value).resolve())
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", default="max")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    args.no_shell = True
    identity = json.loads((args.kit / "kit.json").read_bytes())
    if identity["source_commit"] != PACKAGE_COMMIT:
        parser.error("The installed package receipt must match the sealed candidate commit")
    args.server = (args.kit / "bin/design-mcp").resolve(strict=True)
    if not args.server.is_relative_to(args.kit / "tools/design-mcp"):
        parser.error("The executable must belong to the verified install kit")
    client = subprocess.check_output([args.codex, "--version"], text=True, env=generate.clean_env()).strip()
    cases = list(pilot_cases())
    args.out.mkdir(parents=True)
    args.scratch = args.out / "empty-client-workspace"
    args.scratch.mkdir()
    for case, brief in cases:
        generate.check_quota(args.quota_probe, args.out)
        arms = ["plain", "design-mcp"]
        random.Random(case).shuffle(arms)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [pool.submit(run_draft, args, case, brief, arm, client) for arm in arms]
            for result in results:
                result.result()


if __name__ == "__main__":
    main()
