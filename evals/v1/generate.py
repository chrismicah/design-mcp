"""Run matched Design MCP generation cells and retain success and failure evidence."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent
HOSTED_API_ENV = ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE")
PROMPT = """Build the UI in the brief below. Produce one complete HTML document with inline CSS and JavaScript. Return it in a single html code fence. Keep interactions local and use only the supplied facts. Google Fonts stylesheets are allowed. Use original inline illustrations or CSS for visuals. Do not use other remote assets, imports, or calls. The review runs in Chrome at widths of 1440 and 390 pixels. If a design context tool is available, consult it before creating the UI. Do not write files or call other tools.

Brief:
{brief}
"""


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def clean_env():
    return {key: value for key, value in os.environ.items() if key not in HOSTED_API_ENV}


def check_quota(probe, output):
    receipt = output / f"quota-{time.time_ns()}.json"
    result = subprocess.run([sys.executable, "-I", "-B", str(probe), "--out", str(receipt), "--check-dispatch"],
                            env=clean_env(), timeout=45)
    if result.returncode:
        raise SystemExit(f"Subscription quota probe blocked dispatch. See {receipt}")


def client_command(args, mcp_config):
    return [
        args.codex, "-a", "never", "exec", "--ignore-user-config", "--ephemeral",
        "--skip-git-repo-check", "--sandbox", "read-only", "--json", "-m", args.model,
        "-c", 'model_provider="openai"', "-c", 'service_tier="default"',
        "-c", 'web_search="disabled"', "-c", 'features.fast_mode=false',
        "-c", f'model_reasoning_effort="{args.effort}"', "-c", mcp_config, "-",
    ]


def mcp_table(command, name, server_args, server_env):
    environment = ",".join(f"{json.dumps(key)}={json.dumps(value)}" for key, value in server_env.items())
    return (f"mcp_servers={{{json.dumps(name)}={{command={json.dumps(str(command))},"
            f"args={json.dumps(server_args)},required=true,default_tools_approval_mode=\"writes\","
            f"env={{{environment}}}}}}}")


def hosted_mcp_table(url, name):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError("The hosted comparator must be a public HTTPS endpoint")
    return (f"mcp_servers={{{json.dumps(name)}={{url={json.dumps(url)},required=true,"
            'default_tools_approval_mode="writes"}}')


def read_trace(path):
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def parse_cell(events, expect_mcp, server_name="design-mcp", expected_tool="direct"):
    result = {}
    completed_items = [event["item"] for event in events if event.get("type") == "item.completed"]
    turn = next((e for e in reversed(events) if e.get("type") == "turn.completed"), {})
    result["usage"] = turn.get("usage")
    result["tool_calls"] = [
        {k: item.get(k) for k in ("type", "server", "tool", "status")}
        for item in completed_items
        if item.get("type", "").endswith("_call") or item.get("type") == "command_execution"
    ]
    messages = [i["text"] for i in completed_items if i.get("type") == "agent_message"]
    failures = [e.get("message") or e.get("error") for e in events if e.get("type") == "error"]
    failures.extend(i.get("error") for i in completed_items if i.get("status") == "failed")
    result["client_errors"] = [f for f in failures if f]
    result["treatment_call"] = any(
        item.get("type") == "mcp_tool_call" and item.get("server") == server_name
        and item.get("tool") == expected_tool and item.get("status") == "completed" and not item.get("error")
        for item in completed_items
    )
    if server_name == "design-mcp" and expected_tool == "direct":
        result["direct_call"] = result["treatment_call"]
    result["status"] = "passed"
    if not turn:
        result["status"] = "generation-error"
    elif any(call["type"] != "mcp_tool_call" for call in result["tool_calls"]):
        result["status"] = "unpermitted-tool-call"
    elif not expect_mcp and result["tool_calls"]:
        result["status"] = "control-tool-leak"
    elif expect_mcp and not result["treatment_call"]:
        result["status"] = "mcp-unused-or-failed"
    match = re.fullmatch(r"\s*```html\s*\n(.*)\n```\s*", messages[-1], re.S | re.I) if messages else None
    html = match.group(1) + "\n" if match else None
    if not html or not re.search(r"<body(?:\s[^>]*)?>", html, re.I):
        html = None
        if result["status"] == "passed":
            result["status"] = "invalid-html"
    return result, html


def run_cell(args, case, arm):
    cell = args.out / case["id"] / arm
    cell.mkdir(parents=True, exist_ok=True)
    prompt = PROMPT.format(brief=case["brief"])
    config = args.mcp_config if arm != "none" else "mcp_servers={}"
    identity = dict(case=case["id"], arm=arm, model=args.model, effort=args.effort, client=args.client_version,
                    prompt_sha256=sha256(prompt.encode()))
    if arm not in {"none", "v2"}:
        identity["mcp_config_sha256"] = sha256(config.encode())
    if (cell / "receipt.json").exists():
        receipt = json.loads((cell / "receipt.json").read_text(encoding="utf-8"))
        if any(receipt.get(key) != value for key, value in identity.items()):
            raise RuntimeError(f"The run configuration changed for {cell}. Use a new output directory.")
        return receipt
    if any(cell.iterdir()):
        raise RuntimeError(f"Preserve the interrupted attempt at {cell}. Resume with a new output directory.")
    (cell / "prompt.txt").write_text(prompt, encoding="utf-8")
    trace_path = cell / "client.jsonl"
    start = time.monotonic()
    timed_out = False
    with trace_path.open("w", encoding="utf-8") as trace, (cell / "client.stderr").open("w", encoding="utf-8") as err:
        try:
            process = subprocess.run(client_command(args, config), input=prompt, text=True, stdout=trace,
                                     stderr=err, env=clean_env(), cwd=args.scratch, timeout=args.timeout)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            exit_code = None
            timed_out = True
    result, html = parse_cell(read_trace(trace_path), expect_mcp=arm != "none", server_name=args.server_name,
                              expected_tool=args.expected_tool)
    if timed_out:
        result["status"] = "timeout"
    elif exit_code:
        result["status"] = "client-error"
    result.update(
        identity,
        elapsed_seconds=round(time.monotonic() - start, 2), exit_code=exit_code,
        trace_sha256=sha256(trace_path.read_bytes()),
    )
    if html:
        (cell / "index.html").write_bytes(html.encode())
        result["html_sha256"] = sha256(html.encode())
    (cell / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def run_case(args, case):
    arms = [args.treatment] if args.treatment_only else ["none", args.treatment]
    random.Random(case["id"]).shuffle(arms)
    failed = False
    for arm in arms:
        result = run_cell(args, case, arm)
        print(json.dumps({key: result[key] for key in ("case", "arm", "status", "usage", "elapsed_seconds")}), flush=True)
        failed |= result["status"] != "passed"
        if result["status"] == "client-error" and not result["usage"]:
            # One bad login or service configuration may affect the entire batch.
            raise RuntimeError("Client error without usage. Inspect the preserved trace before dispatching again.")
    return failed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=lambda path: Path(path).resolve())
    server = p.add_mutually_exclusive_group(required=True)
    server.add_argument("--server", type=lambda path: Path(path).resolve())
    server.add_argument("--server-url", help="Public credential-free HTTPS endpoint for a separate hosted comparator")
    p.add_argument("--competitor-config", type=Path, help="JSON object with name, args, env and expected_tool")
    p.add_argument("--treatment-only", action="store_true", help="Reuse sealed controls from the same benchmark")
    p.add_argument("--treatment-label", help="Output arm name for an isolated build of Design MCP")
    p.add_argument("--codex", default="codex")
    p.add_argument("--model", required=True)
    p.add_argument("--effort", default="max")
    p.add_argument("--case", action="append")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--jobs", type=int, choices=(1, 2), default=1, help="Concurrent cases in this batch")
    p.add_argument("--quota-probe", type=lambda path: Path(path).resolve(),
                   help="Python quota probe that supports --out and --check-dispatch")
    args = p.parse_args()
    args.treatment = "v2"
    args.server_name = "design-mcp"
    args.server_args = ["serve"]
    args.server_env = {"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"}
    args.expected_tool = "direct"
    if args.competitor_config:
        competitor = json.loads(args.competitor_config.read_text(encoding="utf-8"))
        name = competitor["name"]
        if not isinstance(name, str) or name in {"none", "v2", "design-mcp"} or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name):
            p.error("Competitor name must be a distinct lowercase slug")
        args.treatment = name
        args.server_name = name
        args.server_args = competitor.get("args", [])
        args.server_env = competitor.get("env", {})
        args.expected_tool = competitor["expected_tool"]
        if not isinstance(args.server_args, list) or not all(isinstance(value, str) for value in args.server_args):
            p.error("Competitor args must be an array of strings")
        if not isinstance(args.server_env, dict) or not all(isinstance(value, str) for value in args.server_env.values()):
            p.error("Competitor env must be an object with string values")
        if not isinstance(args.expected_tool, str) or not args.expected_tool:
            p.error("Competitor expected_tool must name a tool")
    if args.treatment_label:
        if args.competitor_config or args.treatment_label == "none" or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,47}", args.treatment_label
        ):
            p.error("Treatment labels must be lowercase slugs and cannot be combined with a competitor config")
        args.treatment = args.treatment_label
    if args.server_url:
        if not args.competitor_config or args.server_args or args.server_env:
            p.error("A hosted comparator requires a separate name and tool in --competitor-config")
        try:
            args.mcp_config = hosted_mcp_table(args.server_url, args.server_name)
        except ValueError as error:
            p.error(str(error))
    else:
        args.mcp_config = mcp_table(args.server, args.server_name, args.server_args, args.server_env)
    args.client_version = subprocess.check_output([args.codex, "--version"], text=True, env=clean_env()).strip()
    args.scratch = args.out / ".empty-client-workspace"
    args.scratch.mkdir(parents=True, exist_ok=True)
    args.scratch = args.scratch.resolve()
    tasks = json.loads((BASE_DIR / "tasks.json").read_text(encoding="utf-8"))
    if args.case:
        requested = set(args.case)
        tasks = [case for case in tasks if case["id"] in requested]
        if requested != {case["id"] for case in tasks}:
            p.error("Unknown case ID")
    failed = False
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        # Dispatch only one wave at a time so a provider failure cannot burn the entire batch.
        for start in range(0, len(tasks), args.jobs):
            batch = tasks[start:start + args.jobs]
            if args.quota_probe:
                check_quota(args.quota_probe, args.out)
            failed |= any(list(pool.map(lambda case: run_case(args, case), batch)))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
