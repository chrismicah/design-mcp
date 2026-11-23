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
    fixtures = json.loads(Path(__file__).with_name("tasks.json").read_bytes())
    cases = {}
    with TemporaryDirectory() as cwd:
        async with Client(StdioTransport(
            command=executable,
            args=["serve"],
            env={"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"},
            cwd=cwd,
        ), timeout=20) as client:
            tools = [tool.name for tool in await client.list_tools()]
            assert set(tools) == {"direct", "react", "check"}
            for fixture in fixtures:
                brief = fixture["brief"]
                reply = (await client.call_tool("direct", {"brief": brief})).structured_content
                assert reply["direction"]["id"] == "direct-consultation"
                assert reply["direction"]["surface"] == "landing" and not reply["questions"]
                override = (await client.call_tool("direct", {"brief": brief, "surface": "form"})).structured_content
                assert override["direction"]["surface"] == "form"
                reply_canonical = json.dumps(reply, ensure_ascii=False, sort_keys=True).encode()
                reply_sha = sha256(reply_canonical).hexdigest()
                assert reply_sha == fixture["reply_sha256"], fixture["id"]
                cases[fixture["id"]] = {"brief_sha256": sha256(brief.encode()).hexdigest(),
                                        "reply_sha256": reply_sha, "reply": reply}
            pricing_brief = "Omit the splash page, but show pricing for two subscription tiers."
            pricing = (await client.call_tool("direct", {"brief": pricing_brief})).structured_content
            assert pricing["direction"]["id"] == "scale-ledger"
            measured = json.loads(Path(__file__).with_name("opening-feedback.json").read_bytes())

            async def react(phrase, **kwargs):
                reply = await client.call_tool(
                    "react", {"direction_id": "direct-consultation", "reaction": phrase, **kwargs}
                )
                return reply.structured_content

            for phrase, expected in measured["old_reaction_parity"].items():
                body = json.dumps(await react(phrase), sort_keys=True).encode()
                assert sha256(body).hexdigest() == expected, phrase
            test = "fit the opening view"
            assert await react(test, opening_view=measured["failed_view"]) == measured["measured_reaction"]
            assert await react(test, opening_view=measured["healthy_view"]) == measured["healthy_reaction"]
            assert await react(test) == measured["missing_measurements"]
    print(json.dumps({
        "candidate": revision,
        "installer": installer,
        "host": {"macos": platform.mac_ver()[0], "arch": platform.machine(), "python": platform.python_version()},
        "cases": cases,
        "tools": sorted(tools),
        "explicit_form_override": True,
        "affirmative_pricing_clause": True,
        "measured_reaction": measured["measured_reaction"],
        "opening_reaction_parity_cases": len(measured["old_reaction_parity"]),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
