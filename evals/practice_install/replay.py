"""Replay a frozen synthetic practice brief through the exact installed command."""

import asyncio
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    executable, revision, installer = sys.argv[1:]
    fixture, = json.loads(Path(__file__).with_name("tasks.json").read_bytes())
    brief = fixture["brief"]
    with TemporaryDirectory() as cwd:
        async with Client(StdioTransport(
            command=executable,
            args=["serve"],
            env={"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"},
            cwd=cwd,
        ), timeout=20) as client:
            tools = [tool.name for tool in await client.list_tools()]
            assert set(tools) == {"direct", "react", "check"}
            reply = (await client.call_tool("direct", {"brief": brief})).structured_content
            assert reply["direction"]["id"] == "direct-consultation"
            assert reply["direction"]["surface"] == "landing" and not reply["questions"]
            override = (await client.call_tool("direct", {"brief": brief, "surface": "form"})).structured_content
            assert override["direction"]["surface"] == "form"
            pricing_brief = "Omit the splash page, but show pricing for two subscription tiers."
            pricing = (await client.call_tool("direct", {"brief": pricing_brief})).structured_content
            assert pricing["direction"]["id"] == "scale-ledger"
    print(json.dumps({
        "candidate": revision,
        "installer": installer,
        "host": {"macos": platform.mac_ver()[0], "arch": platform.machine(), "python": platform.python_version()},
        "case": fixture["id"],
        "brief_sha256": sha256(brief.encode()).hexdigest(),
        "reply": reply,
        "tools": sorted(tools),
        "explicit_form_override": True,
        "affirmative_pricing_clause": True,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
