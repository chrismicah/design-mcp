"""Expose the same Design Library search tools with one fixed retrieval mode."""

import argparse
import asyncio
import os
from pathlib import Path
import subprocess

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StdioTransport
from mcp.types import ToolAnnotations

from probe_competitors import decode_results
from probe_design_library import CONTROLS

PIN = "96310517ffcc484f4f820434c1cf51c16f763cec"
MODES = ("keyword", "hybrid")
READ_ONLY = ToolAnnotations(readOnlyHint=True)


def create_server(upstream, mode):
    server = FastMCP("Design Library", strict_input_validation=True)

    @server.tool(annotations=READ_ONLY)
    async def search_designs(query: str, type: str | None = None, tags: list[str] | None = None,
                             framework: str | None = None, platform: str | None = None,
                             category: str | None = None) -> dict:
        """Find up to three ranked design references. Use a concise task or component query and optional filters."""
        filters = {"type": type, "tags": tags, "framework": framework, "platform": platform, "category": category}
        result = await upstream.call_tool("search_designs", {"query": query, "mode": mode, "limit": 3,
                                          **{key: value for key, value in filters.items() if value is not None}})
        rows = decode_results(result, "results")
        if len(rows) > 3 or any(not isinstance(row, dict) or not row.get("id") for row in rows):
            raise ValueError("Unexpected search rows from the pinned Design Library")
        return {"retrieval_mode": mode, "results": rows}

    @server.tool(annotations=READ_ONLY)
    async def get_design(id: str) -> dict:
        """Open a design by its search ID. Read its source and license before reusing code."""
        result = await upstream.call_tool("get_design", {"id": id})
        data = result.structured_content
        detail = [data] if isinstance(data, dict) and "id" in data else decode_results(result, "results")
        if len(detail) != 1 or detail[0].get("id") != id or detail[0].get("error"):
            raise ValueError("Design Library did not return the requested design")
        return detail[0]

    return server


async def serve(checkout, python, mode):
    env = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
           "OMP_NUM_THREADS": "2", "VECLIB_MAXIMUM_THREADS": "2"}
    if "HF_HOME" in os.environ:
        env["HF_HOME"] = os.environ["HF_HOME"]
    transport = StdioTransport(command=str(python), args=["-I", "-B", "-m", "designlib", "mcp"],
                               cwd=str(checkout), env=env)
    async with Client(transport, timeout=90) as upstream:
        query = dict(CONTROLS)["nonsense"]
        for expected_mode, expected_count in (("keyword", 0), ("hybrid", 3)):
            control = await upstream.call_tool("search_designs", {"query": query, "mode": expected_mode, "limit": 3})
            if len(decode_results(control, "results")) != expected_count:
                raise ValueError("The pinned Design Library index did not distinguish keyword from hybrid")
        await create_server(upstream, mode).run_async(transport="stdio", show_banner=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("mode", choices=MODES)
    args = parser.parse_args()
    git = ["git", "-C", str(args.checkout)]
    if (subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip() != PIN
            or subprocess.check_output([*git, "status", "--porcelain", "--untracked-files=no"]).strip()):
        parser.error(f"Use a clean Design Library checkout pinned at {PIN}")
    asyncio.run(serve(args.checkout.resolve(), args.python.absolute(), args.mode))


if __name__ == "__main__":
    main()
