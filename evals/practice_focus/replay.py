"""Replay the sealed direct replies from an isolated installed executable."""

from asyncio import run
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

SOURCE = json.loads(Path(__file__).with_name("source-replies.json").read_bytes())


async def replay():
    executable, commit, installer, arm = sys.argv[1:]
    assert SOURCE["commits"][arm] == commit
    cases = {}
    with TemporaryDirectory() as cwd:
        async with Client(StdioTransport(
            command=executable,
            args=["serve"],
            env={"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"},
            cwd=cwd,
        ), timeout=25) as client:
            tools = sorted(tool.name for tool in await client.list_tools())
            assert tools == ["check", "direct", "react"]
            for case, fixture in SOURCE["practices"].items():
                brief = fixture["brief"]
                assert sha256(brief.encode()).hexdigest() == fixture["brief_sha256"]
                result = (await client.call_tool("direct", {"brief": brief})).structured_content
                body = json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
                assert result == fixture[arm]
                assert sha256(body).hexdigest() == fixture["reply_sha256"][arm]
                cases[case] = {"reply": result, "reply_sha256": fixture["reply_sha256"][arm]}
    receipt = {"commit": commit, "arm": arm, "installer": installer, "tools": tools,
               "host": {"macos": platform.mac_ver()[0], "arch": platform.machine(), "python": platform.python_version()},
               "cases": cases}
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run(replay())
