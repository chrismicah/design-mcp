"""Send the full frozen UI briefs to a competitor's installed search tool."""

import argparse
import asyncio
import json
from pathlib import Path
from time import monotonic

from generate import BASE_DIR, sha256


def decode_results(reply, result_key):
    """Accept MCP structured data and the text-only shapes used by the pinned servers."""
    data = reply.structured_content
    if data is not None:
        if isinstance(data, dict):
            data = next((data[key] for key in (result_key, "result") if key in data), None)
        if isinstance(data, list):
            return data
    blocks = [block.text for block in reply.content if block.type == "text"]
    if not blocks and reply.content:
        raise ValueError("Search returned media without ranked rows")
    if len(blocks) == 1 and blocks[0].startswith("No results."):
        return []
    parsed = []
    for block in blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError as error:
            raise ValueError("Search returned an unrecognized text result") from error
        if isinstance(value, dict) and result_key in value:
            value = value[result_key]
        if isinstance(value, list):
            parsed.extend(value)
        elif isinstance(value, dict) and ("id" in value or "name" in value or "slug" in value):
            parsed.append(value)
        else:
            raise ValueError("Search returned an unrecognized result shape")
    return parsed


def ranked_identifiers(results):
    if any(not isinstance(row, dict) for row in results):
        raise ValueError("Search result rows must be objects")
    names = ("id", "slug", "title", "name", "category")
    return [{key: row[key][:200] for key in names if isinstance(row.get(key), str)} for row in results]


async def probe(args, tasks):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=args.command[0], args=args.command[1:], cwd=str(args.cwd))
    async with Client(transport, timeout=40) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        search = tools[args.tool]
        rows = []
        for case in tasks:
            started = monotonic()
            row = {"case": case["id"], "surface": case["surface"], "brief_sha256": sha256(case["brief"].encode())}
            try:
                response = await client.call_tool(
                    args.tool, {**args.fields, "query": case["brief"], "limit": 3}, raise_on_error=False
                )
                content = {"structured": response.structured_content,
                           "content": [block.model_dump(mode="json") for block in response.content]}
                wire = json.dumps(content, sort_keys=True).encode()
                row.update(response_bytes=len(wire), response_sha256=sha256(wire))
                if response.is_error:
                    row["status"] = "tool-error"
                else:
                    results = decode_results(response, args.result_key)
                    row.update(status="matches" if results else "empty", result_count=len(results),
                               ranked=ranked_identifiers(results))
            except (TimeoutError, RuntimeError, ValueError) as error:
                row.update(status="protocol-error", error=type(error).__name__)
            row["milliseconds"] = round((monotonic() - started) * 1000)
            rows.append(row)
    annotations = search.annotations.model_dump(by_alias=True, exclude_none=True) if search.annotations else {}
    return {"competitor": args.name, "pin": args.pin, "search": args.tool, "search_annotations": annotations,
            "tool_count": len(tools), "cases": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--result-key", default="results")
    parser.add_argument("--fields", type=json.loads, default={})
    parser.add_argument("command", nargs="+")
    args = parser.parse_args()
    manifest = (BASE_DIR / "tasks.json").read_bytes()
    result = asyncio.run(probe(args, json.loads(manifest)))
    result["tasks_sha256"] = sha256(manifest)
    result["counts"] = {status: sum(row["status"] == status for row in result["cases"])
                        for status in ("matches", "empty", "tool-error", "protocol-error")}
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(args.name, result["counts"])


if __name__ == "__main__":
    main()
