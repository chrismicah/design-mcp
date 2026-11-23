"""Exercise every public tool over stdio and verify a fixture-specific result."""

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


SAMPLE = """<main>
  <h1>Departure board</h1>
  <div class="bg-[#ff0000]" onclick="showTicket()">Show ticket</div>
  <button>Get started</button>
</main>"""
CURRENT_TOOLS = {"direct", "react", "check"}


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
            cases = {
                "direct": (
                    {"brief": "Build a mobile ticket screen for a train rider."},
                    lambda body: body["direction"]["id"] == "platform-sign",
                ),
                "react": (
                    {"direction_id": "platform-sign", "reaction": "calmer"},
                    lambda body: 0 < body["changes"]["type_ratio"] < 3.5,
                ),
                "check": (
                    {"source_code": SAMPLE},
                    lambda body: any(row["rule"] == "generic-cta" for row in body["findings"]),
                ),
                "search_design_patterns": (
                    {"query": "stripe", "page_type": "Dashboard", "fields": ["name", "page_type"], "limit": 1},
                    lambda body: any(
                        row["page_type"] == "Dashboard" and "stripe" in row["name"].lower()
                        for row in body["result"]
                    ),
                ),
                "get_design_blueprint": (
                    {"pattern_id": "seed-stripe-dashboard"},
                    lambda body: body["id"] == "seed-stripe-dashboard" and body["layout_type"] == "sidebar_main",
                ),
                "get_semantic_tokens": (
                    {"primary_color": "#793c22", "color_mode": "light"},
                    lambda body: body["tokens"]["color-primary"] == "#793c22",
                ),
                "get_design_taxonomy": (
                    {},
                    lambda body: "Dashboard" in body["page_types"],
                ),
                "get_behavioral_pattern": (
                    {"pattern_name": "empty_state"},
                    lambda body: "primary_cta" in body["required_elements"],
                ),
                "compare_design_approaches": (
                    {"page_type": "Dashboard", "limit": 1},
                    lambda body: any(
                        row["page_type"] == "Dashboard"
                        and row["layout_type"]
                        and row["layout_type"] in body["summary"]
                        for row in body["examples"]
                    ),
                ),
                "analyze_and_devibecode": (
                    {"source_code": SAMPLE},
                    lambda body: any("missing role" in finding for finding in body["anti_patterns_found"]),
                ),
                "get_design_system": (
                    {"page_type": "Dashboard"},
                    lambda body: any(
                        "full width" in rule
                        for rule in body["composition_rules"]["dashboard_composition"]["grid_rules"]
                    ),
                ),
                "get_library_recommendations": (
                    {"use_case": "dashboard"},
                    lambda body: any(row["name"] == "Recharts" for row in body["recommendations"]),
                ),
                "get_library_details": (
                    {"library_name": "shadcn-ui"},
                    lambda body: body["library"]["id"] == "shadcn-ui" and "Button" in body["library"]["components"],
                ),
                "scan_project": (
                    {"project_path": folder, "max_files": 1},
                    lambda body: any(
                        row["file"] == "index.html"
                        and any(finding["type"] == "interactive_div" for finding in row["findings"])
                        for row in body["file_reports"]
                    ),
                ),
                "generate_refactored_code": (
                    {"source_code": SAMPLE},
                    lambda body: any(
                        "<Button " in row.get("code_hint", "") for row in body["transformations"]
                    ),
                ),
                "get_visual_recipe": (
                    {"page_type": "Dashboard"},
                    lambda body: "tabular-nums" in body["component_design"]["data_table"]["amounts"],
                ),
                "get_visual_suggestions": (
                    {"source_code": SAMPLE},
                    lambda body: body["color_palette"]["primary"]["hex"] == "#ff0000",
                ),
            }
            expected = {"v2": CURRENT_TOOLS, "legacy": cases.keys() - CURRENT_TOOLS, "both": set(cases)}[mode]
            if review_enabled:
                expected = expected | {"review_page"}
            advertised = {tool.name for tool in tools}
            assert advertised == expected, (
                f"Tool list mismatch (missing {expected - advertised}, unexpected {advertised - expected})"
            )

            for tool in tools:
                name = tool.name
                start = monotonic()
                if name == "review_page":
                    result = await client.call_tool(
                        name, {"url": "file:///design-mcp-smoke"}, raise_on_error=False
                    )
                    body = result.structured_content
                    if (not result.is_error or not body or body.get("ok") is not False
                            or body.get("code") != "unsupported-url"):
                        raise RuntimeError("review_page did not reject a non-web URL")
                    if any(item.type != "text" for item in result.content):
                        raise RuntimeError("Rejected browser reviews must return only text")
                else:
                    if name in CURRENT_TOOLS:
                        assert tool.annotations is not None, f"{name} has no capability annotations"
                        # The wire names are stable across FastMCP 4.1 and 4.2.
                        annotations = tool.annotations.model_dump(by_alias=True)
                        assert annotations.get("readOnlyHint") is True, f"{name} must advertise read-only behavior"
                        assert annotations.get("openWorldHint") is False, f"{name} runs entirely on local data"
                    request, matches_fixture = cases[name]
                    response = await client.call_tool(name, request)
                    body = response.structured_content
                    if not body or body.get("error"):
                        raise RuntimeError(f"{name}: {body!r}")
                    try:
                        matches = matches_fixture(body)
                    except (AttributeError, KeyError, TypeError):
                        matches = False
                    if not matches:
                        raise RuntimeError(f"{name} response did not match the smoke fixture ({repr(body)[:1000]})")
                outcomes[name] = {"keys": list(body), "milliseconds": round((monotonic() - start) * 1000)}
    print(json.dumps({"fastmcp": version("fastmcp"), "mode": mode, "tools": outcomes}, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
