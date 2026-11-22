"""Verify the fixed-mode visual adapter against the installed semantic index."""

import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from time import monotonic

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from probe_design_library import CONTROLS, MODES


async def check(args):
    adapter = Path(__file__).with_name("design_library_mode.py")
    reports = {}
    catalogs = {}
    queries = (("checkout", "ecommerce checkout"), ("pottery", "pottery"), CONTROLS[-1])
    for mode in MODES:
        start = monotonic()
        transport = StdioTransport(
            command=sys.executable,
            args=["-B", str(adapter), "--checkout", str(args.checkout), "--python", str(args.python), mode],
            env={"HF_HOME": os.environ["HF_HOME"]},
        )
        async with Client(transport, timeout=110) as client:
            tools = await client.list_tools()
            catalogs[mode] = [tool.model_dump(mode="json") for tool in tools]
            assert [tool.name for tool in tools] == ["search_designs", "get_design"]
            assert all(tool.annotations.readOnlyHint for tool in tools)
            assert "mode" not in tools[0].input_schema["properties"]
            reports[mode] = {"startup_ms": round((monotonic() - start) * 1000, 1), "queries": {}}
            changed = await client.call_tool("search_designs", {"query": "pottery", "mode": "other"}, raise_on_error=False)
            assert changed.is_error
            for name, text in queries:
                start = monotonic()
                reply = await client.call_tool("search_designs", {"query": text})
                elapsed = round((monotonic() - start) * 1000, 1)
                result = reply.structured_content
                assert result["retrieval_mode"] == mode
                rows = result["results"]
                assert len(rows) <= 3
                outcome = {"query": text, "elapsed_ms": elapsed,
                           "ranked": [{"id": row["id"], "title": row["title"]} for row in rows]}
                if rows and name != "nonsense":
                    first = rows[0]["id"]
                    detail = await client.call_tool("get_design", {"id": first})
                    assert detail.structured_content["id"] == first
                    outcome["read_id"] = first
                    outcome["detail_sha256"] = sha256(json.dumps(detail.structured_content, sort_keys=True).encode()).hexdigest()
                reports[mode]["queries"][name] = outcome
    assert catalogs["keyword"] == catalogs["hybrid"]
    assert all(report["queries"]["checkout"]["read_id"] for report in reports.values())
    assert reports["keyword"]["queries"]["nonsense"]["ranked"] == []
    assert len(reports["hybrid"]["queries"]["nonsense"]["ranked"]) == 3
    return {"tools_identical": True,
            "tool_schema_sha256": sha256(json.dumps(catalogs["keyword"], sort_keys=True).encode()).hexdigest(),
            "modes": reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("checkout", "python", "out"):
        parser.add_argument(f"--{key}", required=True, type=lambda path: Path(path).absolute())
    args = parser.parse_args()
    result = asyncio.run(check(args))
    args.out.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
