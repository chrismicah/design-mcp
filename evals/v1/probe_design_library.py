"""Compare two search modes in one installed, pinned Design Library server."""

import argparse
import asyncio
import json
from pathlib import Path
from time import monotonic

from probe_competitors import BASE_DIR, decode_results, ranked_identifiers, sha256


CONTROLS = (
    ("checkout", "mobile checkout progress"),
    ("settings", "accessible account settings error state"),
    ("pricing", "B2B pricing comparison"),
    ("nonsense", "zzqv_74f18"),
)
MODES = ("keyword", "hybrid")


async def search(client, query, mode):
    started = monotonic()
    reply = await client.call_tool("search_designs", {"query": query, "mode": mode, "limit": 3})
    elapsed = round((monotonic() - started) * 1000, 1)
    rows = decode_results(reply, "results")
    if len(rows) > 3:
        raise ValueError(f"{mode} ignored the three-result limit")
    wire = json.dumps({
        "structured": reply.structured_content,
        "content": [item.model_dump(mode="json") for item in reply.content],
    }, sort_keys=True).encode()
    ranked = ranked_identifiers(rows)
    for item, row in zip(ranked, rows, strict=True):
        item.update({key: row[key] for key in ("type", "platform", "categories", "has_code") if key in row})
    return {"milliseconds": elapsed, "response_bytes": len(wire),
            "response_sha256": sha256(wire), "ranked": ranked}


async def probe(executable, cwd, cases):
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=str(executable), args=["-m", "designlib", "mcp"], cwd=str(cwd))
    started = monotonic()
    async with Client(transport, timeout=90) as client:
        tools = await client.list_tools()
        catalog_ms = round((monotonic() - started) * 1000, 1)
        tool, = (tool for tool in tools if tool.name == "search_designs")
        first_hybrid = await search(client, CONTROLS[0][1], "hybrid")
        results = []
        for index, case in enumerate(cases):
            order = MODES if index % 2 == 0 else MODES[::-1]
            item = {"case": case["id"], "surface": case["surface"],
                    "brief_sha256": sha256(case["brief"].encode()), "mode_order": order}
            for mode in order:
                item[mode] = await search(client, case["brief"], mode)
            results.append(item)
    return {"catalog_ms": catalog_ms, "tools": sorted(tool.name for tool in tools),
            "search_schema": tool.input_schema, "first_hybrid": first_hybrid, "cases": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    manifest = (BASE_DIR / "tasks.json").read_bytes()
    cases = json.loads(manifest) + [
        {"id": f"control-{name}", "surface": "control", "brief": query} for name, query in CONTROLS
    ]
    report = asyncio.run(probe(args.executable, args.cwd, cases))
    report["tasks_sha256"] = sha256(manifest)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
