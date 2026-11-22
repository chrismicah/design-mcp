"""Exercise every public tool through a source worktree's stdio client."""

import asyncio
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


SAMPLE = "<main><h1>Departure board</h1><button>Show ticket</button></main>"


async def main():
    command = sys.argv[1] if len(sys.argv) > 1 else sys.executable
    arguments = sys.argv[2:] or ["-m", "design_mcp.cli", "serve"]
    review_enabled = "--review" in arguments
    outcomes = {}
    with TemporaryDirectory(prefix="design-mcp-smoke-") as folder:
        Path(folder, "index.html").write_text(SAMPLE, encoding="utf-8")
        surface = os.environ.get("DESIGN_MCP_SURFACE")
        mode = "v2" if surface is None else surface.strip().lower()
        env = {"FASTMCP_SHOW_SERVER_BANNER": "false"}
        if surface is not None:
            env["DESIGN_MCP_SURFACE"] = mode
        transport = StdioTransport(command=command, args=arguments, env=env)
        async with Client(transport, timeout=30) as client:
            tools = await client.list_tools()
            handlers = {
                "direct": {"brief": "Build a mobile ticket screen for a train rider."},
                "react": {"direction_id": "platform-sign", "reaction": "calmer"},
                "check": {"source_code": SAMPLE},
                "search_design_patterns": {"query": "dashboard", "limit": 1},
                "get_design_blueprint": {"pattern_id": "seed-stripe-dashboard"},
                "get_semantic_tokens": {"primary_color": "#793C22"},
                "get_design_taxonomy": {},
                "get_behavioral_pattern": {"pattern_name": "empty_state"},
                "compare_design_approaches": {"page_type": "Dashboard", "limit": 1},
                "analyze_and_devibecode": {"source_code": SAMPLE},
                "get_design_system": {"page_type": "Dashboard"},
                "get_library_recommendations": {"use_case": "dashboard"},
                "get_library_details": {"library_name": "shadcn-ui"},
                "scan_project": {"project_path": folder, "max_files": 1},
                "generate_refactored_code": {"source_code": SAMPLE},
                "get_visual_recipe": {"page_type": "Dashboard"},
                "get_visual_suggestions": {"source_code": SAMPLE},
            }
            for tool in tools:
                name = tool.name
                if name == "review_page":
                    start = monotonic()
                    result = await client.call_tool(
                        name, {"url": "file:///design-mcp-smoke"}, raise_on_error=False
                    )
                    body = result.structured_content
                    if not result.is_error or not body or body.get("ok") is not False:
                        raise RuntimeError("review_page did not reject a non-web URL")
                    if any(item.type != "text" for item in result.content):
                        raise RuntimeError("Rejected browser reviews must return only text")
                    outcomes[name] = {"keys": list(body), "milliseconds": round((monotonic() - start) * 1000)}
                    continue
                if name in {"direct", "react", "check"}:
                    annotations = tool.annotations
                    assert annotations is not None, f"{name} has no capability annotations"
                    assert annotations.readOnlyHint is True, f"{name} must advertise read-only behavior"
                    assert annotations.openWorldHint is False, f"{name} runs entirely on local data"
                start = monotonic()
                response = await client.call_tool(name, handlers[name])
                body = response.structured_content
                if not body or body.get("error"):
                    raise RuntimeError(f"{name}: {body!r}")
                outcomes[name] = {"keys": list(body), "milliseconds": round((monotonic() - start) * 1000)}
    assert ("review_page" in outcomes) == review_enabled
    assert len(outcomes) == {"legacy": 14, "both": 17, "v2": 3}[mode] + review_enabled
    print(json.dumps({"fastmcp": version("fastmcp"), "mode": mode, "tools": outcomes}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
