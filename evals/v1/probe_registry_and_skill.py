"""Run the frozen briefs against the shadcn registry and UI UX Pro Max search."""

import argparse
import asyncio
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic

from generate import BASE_DIR, shadcn_item_names, sha256


SHADCN_ITEM = re.compile(r"^- ([\w@][\w./@-]*) (?:\(([^)]+)\))?", re.M)
SKILL_FIELDS = ("Style Category", "Pattern Name", "Product Type", "Guideline", "Category",
                "Font Pairing Name", "Pattern", "Topic", "Name")
SHADCN_QUERY_KINDS = ("full_brief", "task_query", "component_name")


def lines(text):
    return [{"name": match.group(1), "type": match.group(2)} for match in SHADCN_ITEM.finditer(text)]


def row_for(case, data, status, results, started, **extra):
    return {"case": case["id"], "surface": case.get("surface"), "brief_sha256": sha256(case["brief"].encode()),
            "response_bytes": len(data), "response_sha256": sha256(data), "status": status,
            "result_count": len(results), "ranked": results,
            "milliseconds": round((monotonic() - started) * 1000), **extra}


async def shadcn(cwd, launch, tasks):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=str(launch), args=["mcp"], cwd=str(cwd))
    async with Client(transport, timeout=35) as client:
        tools = {item.name: item for item in await client.list_tools()}
        search = "search_items_in_registries"
        schema = tools[search].model_dump(by_alias=True, exclude_none=True)["inputSchema"]

        async def get(case):
            started = monotonic()
            response = await client.call_tool(search, {"query": case["brief"], "limit": 3, "registries": ["@shadcn"]},
                                              raise_on_error=False)
            text = "\n".join(block.text for block in response.content if block.type == "text")
            items = lines(text) if text.startswith("Found ") else []
            status = "tool-error" if response.is_error else "matches" if items else (
                "empty" if text.startswith("No items found matching") else "unrecognized-response")
            return row_for(case, text.encode(), status, items, started,
                           response_prefix=text[:180] if not items and status != "empty" else None)

        positive = await get({"id": "known-control", "brief": "accordion"})
        assert positive["status"] == "matches", positive
        negative = await get({"id": "nonsense-control", "brief": "zqxj27vtg56_unknown_component"})
        return {"tool": search, "tool_count": len(tools), "input_schema": schema,
                "controls": [positive, negative], "cases": [await get(task) for task in tasks]}


async def shadcn_maintenance(cwd, launch, tasks):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    case = next(task for task in tasks if task["id"] == "form-maintenance")
    config = json.loads((BASE_DIR / "shadcn-maintenance.json").read_bytes())
    components = ["field", "input", "textarea", "radio-group"]
    search = "search_items_in_registries"
    view = "view_items_in_registries"
    examples = "get_item_examples_from_registries"
    registry = {"registries": ["@shadcn"]}
    calls = [
        ("frozen-brief", search, {**registry, "query": case["brief"], "limit": 3}, set()),
        ("named-search", search, {**registry, "query": "field", "types": ["ui"], "limit": 3}, {"field"}),
        ("named-details", view, {"items": [f"@shadcn/{name}" for name in components]}, set(components)),
        ("named-example", examples, {**registry, "query": "field-demo"}, {"field-demo"}),
        ("nonsense", search, {**registry, "query": "qzx61-no-such-component", "limit": 3}, set()),
    ]
    transport = StdioTransport(command=str(launch), args=["mcp"], cwd=str(cwd))
    rows = {}
    async with Client(transport, timeout=35) as client:
        installed_tools = {item.name for item in await client.list_tools()}
        assert set(config["verified_read_only_tools"]) <= installed_tools
        for label, tool, arguments, expected in calls:
            started = monotonic()
            reply = await client.call_tool(tool, arguments, raise_on_error=False)
            result = {"content": [block.model_dump(mode="json", by_alias=True) for block in reply.content],
                      "isError": reply.is_error}
            names = shadcn_item_names({"tool": tool, "arguments": arguments, "result": result})
            matched = sorted(names.intersection(config["required_shadcn_items"]))
            raw = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
            text = "\n".join(block.text for block in reply.content if block.type == "text")
            status = (
                "tool-error" if reply.is_error else "matches" if names
                else "empty" if text.startswith("No items found") else "unrecognized"
            )
            valid = expected <= names and status in {"empty", "matches"}
            if label == "nonsense":
                valid = status == "empty"
            rows[label] = {
                "tool": tool,
                "arguments_sha256": sha256(json.dumps(arguments, ensure_ascii=False, sort_keys=True).encode()),
                "payload_sha256": sha256(raw),
                "response_bytes": len(raw),
                "status": status,
                "returned_names": sorted(names),
                "matching_preregistered_items": matched,
                "passed": valid,
                "milliseconds": round((monotonic() - started) * 1000),
            }
            if not valid:
                rows[label]["response_prefix"] = text[:1200]
    return {"scope": "Installed shadcn stdio retrieval and relevance gate. No model or render.",
            "case": case["id"], "brief_sha256": sha256(case["brief"].encode()), "calls": rows}


async def shadcn_task_queries(cwd, launch, tasks, plan):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    if set(plan) != {case["id"] for case in tasks}:
        raise ValueError("Declare one query and relevant components for each frozen brief")
    tool = "search_items_in_registries"
    transport = StdioTransport(command=str(launch), args=["mcp"], cwd=str(cwd))
    async with Client(transport, timeout=35) as client:
        tools = await client.list_tools()
        assert any(item.name == tool for item in tools)

        async def search(query, expected):
            started = monotonic()
            arguments = {"query": query, "limit": 3, "registries": ["@shadcn"], "types": ["ui"]}
            response = await client.call_tool(tool, arguments, raise_on_error=False)
            result = {"content": [block.model_dump(mode="json", by_alias=True) for block in response.content],
                      "isError": response.is_error}
            text = "\n".join(block.text for block in response.content if block.type == "text")
            names = shadcn_item_names({"tool": tool, "arguments": arguments, "result": result})
            status = ("tool-error" if response.is_error else "matches" if names
                      else "empty" if text.startswith("No items found") else "unrecognized-response")
            return {
                "status": status, "returned_names": sorted(names), "matched": sorted(names.intersection(expected)),
                "milliseconds": round((monotonic() - started) * 1000),
                "query_sha256": sha256(query.encode()), "response_sha256": sha256(text.encode()),
                "response_bytes": len(text.encode()),
            }

        controls = {"known": await search("accordion", {"accordion"}),
                    "nonsense": await search("qzx61-no-such-component", set())}
        cases = []
        for index, case in enumerate(tasks):
            target = plan[case["id"]]
            expected = set(target["components"])
            queries = list(zip(SHADCN_QUERY_KINDS, (case["brief"], target["query"], target["components"][0]),
                               strict=True))
            offset = index % len(queries)
            queries = queries[offset:] + queries[:offset]
            outcomes = {kind: await search(query, expected) for kind, query in queries}
            cases.append({"case": case["id"], "surface": case["surface"], **outcomes})
    return {
        "scope": "Installed shadcn UI-registry retrieval. Each brief, short query and first preregistered component name were searched in the same session.",
        "tool": tool, "controls": controls, "cases": cases,
        "counts": {kind: {
            "relevant": sum(bool(case[kind]["matched"]) for case in cases),
            **{status: sum(case[kind]["status"] == status for case in cases)
               for status in ("matches", "empty", "tool-error", "unrecognized-response")},
        } for kind in SHADCN_QUERY_KINDS},
    }


def skill(cwd, launch, tasks):
    def get(case):
        started = monotonic()
        result = subprocess.run([sys.executable, "-B", str(launch), case["brief"], "--max-results", "3", "--json"],
                                cwd=cwd, capture_output=True, timeout=20)
        if result.returncode:
            return row_for(case, result.stdout, "tool-error", [], started, returncode=result.returncode)
        data = json.loads(result.stdout)
        assert isinstance(data.get("results"), list) or data.get("error"), data
        rows = [{name: row[name] for name in SKILL_FIELDS if isinstance(row.get(name), str)}
                for row in data.get("results", [])]
        status = "tool-error" if data.get("error") else "matches" if rows else "empty"
        return row_for(case, result.stdout, status, rows, started, domain=data.get("domain"),
                       detected_domain=data.get("auto_detected"))

    positive = get({"id": "known-control", "brief": "glassmorphism"})
    assert positive["status"] == "matches", positive
    negative = get({"id": "nonsense-control", "brief": "zqxj27vtg56_unknown_component"})
    return {"tool": "search.py", "controls": [positive, negative], "cases": [get(task) for task in tasks]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", choices=("shadcn", "ui-ux-pro-max"))
    parser.add_argument("--pin", required=True)
    parser.add_argument("--launch", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--maintenance", action="store_true", help="Probe named shadcn items for the maintenance form")
    mode.add_argument("--task-queries", action="store_true", help="Compare full and short shadcn queries on the frozen briefs")
    args = parser.parse_args()
    manifest = (BASE_DIR / "tasks.json").read_bytes()
    tasks = json.loads(manifest)
    if args.task_queries:
        if args.candidate != "shadcn":
            parser.error("--task-queries applies to shadcn")
        plan = (BASE_DIR / "shadcn-task-queries.json").read_bytes()
        result = asyncio.run(shadcn_task_queries(args.cwd, args.launch, tasks, json.loads(plan)))
        result.update(competitor=args.candidate, pin=args.pin, tasks_sha256=sha256(manifest), plan_sha256=sha256(plan))
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(args.candidate, result["counts"])
        failed = any(group["tool-error"] or group["unrecognized-response"] for group in result["counts"].values())
        if failed or not result["controls"]["known"]["matched"] or result["controls"]["nonsense"]["status"] != "empty":
            raise SystemExit(2)
        return
    if args.maintenance:
        if args.candidate != "shadcn":
            parser.error("--maintenance applies to shadcn")
        result = asyncio.run(shadcn_maintenance(args.cwd, args.launch, tasks))
        result.update(competitor=args.candidate, pin=args.pin, tasks_sha256=sha256(manifest))
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(args.candidate, {name: row["status"] for name, row in result["calls"].items()})
        if not all(row["passed"] for row in result["calls"].values()):
            raise SystemExit(2)
        return
    result = (asyncio.run(shadcn(args.cwd, args.launch, tasks)) if args.candidate == "shadcn"
              else skill(args.cwd, args.launch, tasks))
    result.update(competitor=args.candidate, pin=args.pin, tasks_sha256=sha256(manifest))
    result["counts"] = {status: sum(row["status"] == status for row in result["cases"])
                        for status in ("matches", "empty", "tool-error", "unrecognized-response")}
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(args.candidate, result["counts"])


if __name__ == "__main__":
    main()
