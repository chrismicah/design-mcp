"""Run the frozen briefs against the shadcn registry and UI UX Pro Max search."""

import argparse
import asyncio
import json
from pathlib import Path
import re
import subprocess
import sys
from time import monotonic

from generate import BASE_DIR, sha256


SHADCN_ITEM = re.compile(r"^- ([\w@][\w./@-]*) (?:\(([^)]+)\))?", re.M)
SKILL_FIELDS = ("Style Category", "Pattern Name", "Product Type", "Guideline", "Category",
                "Font Pairing Name", "Pattern", "Topic", "Name")


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
    args = parser.parse_args()
    manifest = (BASE_DIR / "tasks.json").read_bytes()
    tasks = json.loads(manifest)
    result = (asyncio.run(shadcn(args.cwd, args.launch, tasks)) if args.candidate == "shadcn"
              else skill(args.cwd, args.launch, tasks))
    result.update(competitor=args.candidate, pin=args.pin, tasks_sha256=sha256(manifest))
    result["counts"] = {status: sum(row["status"] == status for row in result["cases"])
                        for status in ("matches", "empty", "tool-error", "unrecognized-response")}
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(args.candidate, result["counts"])


if __name__ == "__main__":
    main()
