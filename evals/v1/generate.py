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


def generation_prompt(brief, require_unhinted_direct=False):
    prompt = PROMPT.format(brief=brief)
    if require_unhinted_direct:
        prompt = prompt.replace(
            "\n\nBrief:\n",
            "\nIf the direct tool is available, call it once with the brief below verbatim as its sole argument.\n\nBrief:\n",
            1,
        )
    return prompt


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
    command = [
        args.codex, "-a", "never", "exec", "--ignore-user-config", "--ephemeral",
        "--skip-git-repo-check", "--sandbox", "read-only", "--json", "-m", args.model,
        "-c", 'model_provider="openai"', "-c", 'service_tier="default"',
        "-c", 'web_search="disabled"', "-c", 'features.fast_mode=false',
        "-c", f'model_reasoning_effort="{args.effort}"', "-c", mcp_config,
    ]
    if args.no_shell:
        command += ["-c", "features.shell_tool=false"]
    return [*command, "-"]


def mcp_table(command, name, server_args, server_env, verified_read_only_tools=(), startup_timeout=None):
    environment = ",".join(f"{json.dumps(key)}={json.dumps(value)}" for key, value in server_env.items())
    scoped_tools = ""
    if verified_read_only_tools:
        scoped_tools = f"enabled_tools={json.dumps(verified_read_only_tools)},"
    approval = "approve" if verified_read_only_tools else "writes"
    startup = f"startup_timeout_sec={startup_timeout}," if startup_timeout else ""
    return (f"mcp_servers={{{json.dumps(name)}={{command={json.dumps(str(command))},"
            f"args={json.dumps(server_args)},required=true,{startup}{scoped_tools}default_tools_approval_mode=\"{approval}\","
            f"env={{{environment}}}}}}}")


def hosted_mcp_table(url, name):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
            or parsed.password is not None or parsed.fragment):
        raise ValueError("The hosted comparator must be a public HTTPS endpoint")
    return (f"mcp_servers={{{json.dumps(name)}={{url={json.dumps(url)},required=true,"
            'default_tools_approval_mode="writes"}}')


def loopback_mcp_table(url, name, verified_read_only_tools):
    match = re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})/mcp", url)
    if not match or int(match.group(1)) > 65535 or not verified_read_only_tools:
        raise ValueError("The local comparator needs a loopback /mcp URL and reviewed tools")
    return (f"mcp_servers={{{json.dumps(name)}={{url={json.dumps(url)},required=true,"
            f"enabled_tools={json.dumps(verified_read_only_tools)},"
            'default_tools_approval_mode="approve"}}')


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


def direct_direction(item):
    value = item.get("result")
    if not isinstance(value, dict) or value.get("is_error") or value.get("isError"):
        return None
    for key in ("structured_content", "direction", "id"):
        value = value.get(key) if isinstance(value, dict) else None
    return value if isinstance(value, str) else None


def shadcn_item_names(item):
    """Read names from the pinned shadcn MCP result, excluding queries and empty replies."""
    result = item.get("result")
    if not isinstance(result, dict) or result.get("is_error") or result.get("isError"):
        return set()
    content = result.get("content")
    if not isinstance(content, list):
        return set()
    arguments = item.get("arguments")
    if not isinstance(arguments, dict):
        arguments = {}
    names = set()
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "text" or not isinstance(block.get("text"), str):
            continue
        body = block["text"].strip()
        if item["tool"] == "search_items_in_registries" and re.match(r"Found [1-9][0-9]* items", body):
            _, found, entries = body.partition("\n\nShowing items ")
            if found:
                names.update(re.findall(r"^- ([a-z0-9-]+) \(registry:ui\).* \[@shadcn\]\s*$", entries, re.M))
        elif item["tool"] == "view_items_in_registries" and body.startswith("Item Details:\n"):
            requested = arguments.get("items")
            if not isinstance(requested, list):
                continue
            for section in body.split("\n\n---\n\n"):
                heading = re.search(r"^## ([a-z0-9-]+)$", section, re.M)
                if (heading and f"@shadcn/{heading.group(1)}" in requested
                        and re.search(r"^\*\*Type:\*\* registry:ui$", section, re.M)):
                    names.add(heading.group(1))
        elif item["tool"] == "get_item_examples_from_registries" and body.startswith("# Usage Examples\n"):
            if arguments.get("registries") not in (None, [], ["@shadcn"]):
                continue
            for section in body.split("\n\n---\n\n"):
                heading = re.search(r"^## Example: ([a-z0-9-]+)$", section, re.M)
                code_blocks = re.findall(r"^\x60\x60\x60tsx\n(.*?)^\x60\x60\x60$", section, re.M | re.S)
                if heading and any(code.strip() for code in code_blocks):
                    names.add(heading.group(1))
    return names


def matched_response_text(calls, required_hashes):
    matched = set()
    for item in calls:
        result = item.get("result")
        if item["tool"] not in required_hashes or not isinstance(result, dict):
            continue
        content = result.get("content")
        if result.get("is_error") or result.get("isError") or not isinstance(content, list):
            continue
        parts = [part["text"] for part in content if isinstance(part, dict)
                 and part.get("type") == "text" and isinstance(part.get("text"), str)]
        if parts and sha256("\n".join(parts).strip().encode()) == required_hashes[item["tool"]]:
            matched.add(item["tool"])
    return sorted(matched)


def library_retrieval(calls, mode):
    ranked = set()
    read = set()
    for call in calls:
        result = call.get("result")
        if not isinstance(result, dict) or result.get("is_error") or result.get("isError"):
            continue
        data = result.get("structured_content")
        if not isinstance(data, dict):
            continue
        if call["tool"] == "search_designs":
            if data.get("retrieval_mode") != mode:
                return [], "design-library-mode-mismatch"
            rows = data.get("results")
            if isinstance(rows, list) and 0 < len(rows) <= 3:
                ranked.update(row["id"] for row in rows if isinstance(row, dict) and isinstance(row.get("id"), str))
        elif call["tool"] == "get_design":
            entry_id = data.get("id")
            arguments = call.get("arguments")
            if (isinstance(entry_id, str) and entry_id in ranked and not data.get("error")
                    and isinstance(arguments, dict) and arguments.get("id") == entry_id):
                read.add(entry_id)
    return sorted(read), "passed" if read else "design-library-result-unread"


def uiux_guidance_received(calls):
    for call in calls:
        reply = call.get("result")
        if not isinstance(reply, dict) or reply.get("is_error") or reply.get("isError"):
            continue
        blocks = reply.get("content")
        if not isinstance(blocks, list):
            continue
        for block in blocks:
            if not isinstance(block, dict) or block.get("type") != "text" or not isinstance(block.get("text"), str):
                continue
            body = block["text"].strip()
            if (body.startswith("## Design System: ") and re.search(r"^### Pattern\n- \*\*Name:\*\* \S", body, re.M)):
                return True
            if (body.startswith("## UI Pro Max Search Results\n")
                    and re.search(r"\*\*Found:\*\* [1-9][0-9]* results?\b", body)
                    and re.search(r"^### Result 1\n- \*\*", body, re.M)):
                return True
    return False


def parse_cell(events, expect_mcp, server_name="design-mcp", expected_tool="direct", expected_direction=None,
               required_shadcn_items=(), required_response_text_sha256=None, expected_direct_brief=None,
               design_library_mode=None):
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
    eligible_tools = {expected_tool} if isinstance(expected_tool, str) else set(expected_tool)
    matching_calls = [
        item for item in completed_items if item.get("type") == "mcp_tool_call" and item.get("server") == server_name
        and item.get("tool") in eligible_tools
    ]
    eligible_calls = [item for item in matching_calls if item.get("status") == "completed" and not item.get("error")]
    result["treatment_call"] = bool(eligible_calls)
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
    if expected_direction is not None:
        observed = [direct_direction(item) if item in eligible_calls else None for item in matching_calls]
        result["observed_directions"] = observed
        if result["status"] == "passed" and observed != [expected_direction]:
            result["status"] = "unexpected-design-direction"
    if expected_direct_brief is not None:
        result["unhinted_direct"] = (
            len(result["tool_calls"]) == len(eligible_calls) == 1
            and eligible_calls[0].get("arguments") == {"brief": expected_direct_brief}
        )
        if result["status"] == "passed" and not result["unhinted_direct"]:
            result["status"] = "hinted-or-changed-direct"
    if expect_mcp and required_shadcn_items:
        retrieved = set().union(*(shadcn_item_names(item) for item in eligible_calls))
        matched = sorted(retrieved.intersection(required_shadcn_items))
        result["matched_shadcn_items"] = matched
        if result["status"] == "passed" and not matched:
            result["status"] = "shadcn-relevant-item-missing"
    if expect_mcp and required_response_text_sha256:
        matched = matched_response_text(eligible_calls, required_response_text_sha256)
        result["matched_response_tools"] = matched
        if result["status"] == "passed" and not matched:
            result["status"] = "required-mcp-response-missing"
    if design_library_mode is not None:
        read, status = library_retrieval(eligible_calls, design_library_mode)
        result["read_design_library_ids"] = read
        if result["status"] == "passed":
            result["status"] = status
    if expect_mcp and server_name == "uiux-pro-max":
        result["uiux_guidance_received"] = uiux_guidance_received(eligible_calls)
        if result["status"] == "passed" and not result["uiux_guidance_received"]:
            result["status"] = "uiux-guidance-missing"
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
    unhinted = args.require_unhinted_direct
    prompt = generation_prompt(case["brief"], unhinted)
    config = args.mcp_config if arm != "none" else "mcp_servers={}"
    identity = dict(case=case["id"], arm=arm, model=args.model, effort=args.effort, client=args.client_version,
                    prompt_sha256=sha256(prompt.encode()))
    expected_direction = args.expected_directions.get(case["id"]) if arm != "none" else None
    if expected_direction is not None:
        identity["expected_direction"] = expected_direction
    if unhinted:
        identity["require_unhinted_direct"] = True
    required_shadcn_items = args.required_shadcn_items if arm != "none" else []
    if required_shadcn_items:
        identity["required_shadcn_items"] = required_shadcn_items
    required_response_text_sha256 = args.required_response_text_sha256 if arm != "none" else {}
    if required_response_text_sha256:
        identity["required_response_text_sha256"] = required_response_text_sha256
    mode = getattr(args, "design_library_mode", None) if arm != "none" else None
    if mode:
        identity["design_library_mode"] = mode
    if args.no_shell:
        identity["shell_tool"] = False
    if arm not in {"none", "v2"}:
        identity["mcp_config_sha256"] = sha256(config.encode())
    if (cell / "receipt.json").exists():
        receipt = json.loads((cell / "receipt.json").read_text(encoding="utf-8"))
        if (receipt.get("shell_tool", True) != (not args.no_shell)
                or receipt.get("expected_direction") != expected_direction
                or receipt.get("require_unhinted_direct", False) != unhinted
                or receipt.get("required_shadcn_items", []) != required_shadcn_items
                or receipt.get("required_response_text_sha256", {}) != required_response_text_sha256
                or any(receipt.get(key) != value for key, value in identity.items())):
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
                              expected_tool=args.expected_tool, expected_direction=expected_direction,
                              required_shadcn_items=required_shadcn_items,
                              required_response_text_sha256=required_response_text_sha256,
                              expected_direct_brief=case["brief"] if unhinted and arm != "none" else None,
                              design_library_mode=mode)
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
    server.add_argument("--loopback-server-url", help="Fixture comparator at http://127.0.0.1:PORT/mcp")
    p.add_argument("--competitor-config", type=Path, help="JSON object with name, args, env, and expected_tool or expected_tools")
    p.add_argument("--design-library-mode", choices=("keyword", "hybrid"),
                   help="Fix the mode for the reviewed Design Library stdio adapter")
    p.add_argument("--treatment-only", action="store_true", help="Reuse sealed controls from the same benchmark")
    p.add_argument("--treatment-label", help="Output arm name for an isolated build of Design MCP")
    p.add_argument("--codex", default="codex")
    p.add_argument("--model", required=True)
    p.add_argument("--effort", default="max")
    p.add_argument("--tasks", type=Path, default=BASE_DIR / "tasks.json",
                   help="Use a separate brief set without replacing the frozen tasks")
    p.add_argument("--case", action="append")
    p.add_argument("--expect-direction", action="append", default=[], metavar="CASE=ID",
                   help="Require one Design MCP direct reply with this direction for each selected case")
    p.add_argument("--require-unhinted-direct", action="store_true",
                   help="Require one direct call with the original brief as its sole argument")
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--jobs", type=int, choices=(1, 2), default=1, help="Concurrent cases in this batch")
    p.add_argument("--no-shell", action="store_true", help="Disable command execution for a fresh matched comparison")
    p.add_argument("--quota-probe", type=lambda path: Path(path).resolve(),
                   help="Python quota probe that supports --out and --check-dispatch")
    args = p.parse_args()
    args.treatment = "v2"
    args.server_name = "design-mcp"
    args.server_args = ["serve"]
    args.server_env = {"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"}
    args.expected_tool = "direct"
    args.required_shadcn_items = []
    args.required_response_text_sha256 = {}
    verified_read_only_tools = []
    if args.competitor_config:
        competitor = json.loads(args.competitor_config.read_text(encoding="utf-8"))
        name = competitor["name"]
        if not isinstance(name, str) or name in {"none", "v2", "design-mcp"} or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", name):
            p.error("Competitor name must be a distinct lowercase slug")
        args.treatment = name
        args.server_name = name
        args.server_args = competitor.get("args", [])
        args.server_env = competitor.get("env", {})
        tool = competitor.get("expected_tool")
        tools = competitor.get("expected_tools")
        if not isinstance(args.server_args, list) or not all(isinstance(value, str) for value in args.server_args):
            p.error("Competitor args must be an array of strings")
        if not isinstance(args.server_env, dict) or not all(isinstance(value, str) for value in args.server_env.values()):
            p.error("Competitor env must be an object with string values")
        if isinstance(tool, str) and tool and tools is None:
            args.expected_tool = tool
        elif tool is None and isinstance(tools, list) and tools and all(isinstance(name, str) and name for name in tools):
            args.expected_tool = tuple(tools)
        else:
            p.error("Provide either expected_tool or a nonempty expected_tools array of tool names")
        verified_read_only_tools = competitor.get("verified_read_only_tools", [])
        if not isinstance(verified_read_only_tools, list) or not all(
            isinstance(name, str) and re.fullmatch(r"[a-zA-Z0-9_.-]+", name) for name in verified_read_only_tools
        ):
            p.error("verified_read_only_tools must list the reviewed tool names")
        expected = {args.expected_tool} if isinstance(args.expected_tool, str) else set(args.expected_tool)
        if verified_read_only_tools and not expected.issubset(verified_read_only_tools):
            p.error("Every expected tool must appear in verified_read_only_tools when supplied")
        if "required_shadcn_items" in competitor:
            items = competitor["required_shadcn_items"]
            if (name != "shadcn" or not isinstance(items, list) or not items
                    or not all(isinstance(item, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item)
                               for item in items)):
                p.error("required_shadcn_items requires the shadcn comparator and a nonempty list of item names")
            args.required_shadcn_items = sorted(set(items))
        if "required_response_text_sha256" in competitor:
            hashes = competitor["required_response_text_sha256"]
            if args.case != [competitor.get("case")]:
                p.error("Pass the single --case declared in the comparator response fixture")
            if (not isinstance(hashes, dict) or not hashes or not hashes.keys() <= expected
                    or not all(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                               for digest in hashes.values())):
                p.error("required_response_text_sha256 must map expected tools to SHA-256 digests")
            args.required_response_text_sha256 = hashes
    if args.design_library_mode:
        if (not args.server or args.server_name != "design-library" or args.server_args or args.treatment_label
                or set(args.expected_tool) != {"search_designs", "get_design"}):
            p.error("Use the mode with the Design Library visual adapter, its config and no treatment label")
        args.server_args = [args.design_library_mode]
        args.treatment = f"design-library-{args.design_library_mode}"
    if args.treatment_label:
        if args.competitor_config or args.treatment_label == "none" or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,47}", args.treatment_label
        ):
            p.error("Treatment labels must be lowercase slugs and cannot be combined with a competitor config")
        args.treatment = args.treatment_label
    if args.loopback_server_url:
        if not args.competitor_config or args.server_args or args.server_env or not args.required_response_text_sha256:
            p.error("A loopback comparator requires a tool catalog and response hashes in --competitor-config")
        try:
            args.mcp_config = loopback_mcp_table(args.loopback_server_url, args.server_name, verified_read_only_tools)
        except ValueError as error:
            p.error(str(error))
    elif args.server_url:
        if not args.competitor_config or args.server_args or args.server_env or verified_read_only_tools:
            p.error("A hosted comparator requires a separate name and tool in --competitor-config")
        try:
            args.mcp_config = hosted_mcp_table(args.server_url, args.server_name)
        except ValueError as error:
            p.error(str(error))
    else:
        args.mcp_config = mcp_table(args.server, args.server_name, args.server_args, args.server_env,
                                    verified_read_only_tools, startup_timeout=60 if args.design_library_mode else None)
    tasks = json.loads(args.tasks.read_text(encoding="utf-8"))
    if (not isinstance(tasks, list) or not tasks or
            any(not isinstance(case, dict) or
                not isinstance(case.get("id"), str) or
                not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case["id"]) or
                not isinstance(case.get("brief"), str) or not case["brief"].strip()
                for case in tasks) or len({case["id"] for case in tasks}) != len(tasks)):
        p.error("Tasks must be a nonempty list of unique brief IDs and brief text")
    if args.case:
        requested = set(args.case)
        tasks = [case for case in tasks if case["id"] in requested]
        if requested != {case["id"] for case in tasks}:
            p.error("Unknown case ID")
    args.expected_directions = {}
    if args.require_unhinted_direct and not args.expect_direction:
        p.error("--require-unhinted-direct requires --expect-direction")
    if args.expect_direction:
        if args.competitor_config:
            p.error("--expect-direction is for the Design MCP treatment")
        for entry in args.expect_direction:
            case_id, _, direction = entry.partition("=")
            if case_id in args.expected_directions or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", direction):
                p.error("Each expected direction must be a unique CASE=ID pair")
            args.expected_directions[case_id] = direction
        if args.expected_directions.keys() != {case["id"] for case in tasks}:
            p.error("Provide an expected direction for each selected case")
    args.client_version = subprocess.check_output([args.codex, "--version"], text=True, env=clean_env()).strip()
    args.scratch = args.out / ".empty-client-workspace"
    args.scratch.mkdir(parents=True, exist_ok=True)
    args.scratch = args.scratch.resolve()
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
