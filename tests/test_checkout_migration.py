import os
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport
import pytest

from scripts.stage_legacy_data import INPUTS, stage


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_stage_copies_source_without_replacing_work(tmp_path):
    source = ROOT / "design_mcp" / "data"
    output = tmp_path / "data"
    output.mkdir()
    working_copy = output / "patterns.json"
    working_copy.write_text("[]")

    assert set(stage(source, output)) == set(INPUTS) - {"patterns.json"}
    assert working_copy.read_text() == "[]"
    for name in INPUTS:
        if name != "patterns.json":
            assert (output / name).read_bytes() == (source / name).read_bytes()
    assert stage(source, output) == []


@pytest.mark.asyncio
async def test_checkout_server_entrypoint_keeps_legacy_mode(tmp_path):
    env = {key: value for key, value in os.environ.items() if key != "DESIGN_MCP_SURFACE"}
    launch = StdioTransport(command=sys.executable, args=[str(ROOT / "server.py")], cwd=str(tmp_path), env=env)
    async with Client(launch, timeout=20) as client:
        tools = {tool.name for tool in await client.list_tools()}
        assert len(tools) == 14 and {"search_design_patterns", "get_design_taxonomy"} <= tools
        assert "direct" not in tools
        result = await client.call_tool("get_design_taxonomy", {})
        assert result.structured_content["page_types"]
