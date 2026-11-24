"""Verify consultation routing through a clean installation's stdio entry point."""

import asyncio
from importlib.metadata import distribution
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


def verify_package(checkout: Path, expected_revision: str) -> None:
    package = distribution("design-mcp")
    provenance = json.loads(package.read_text("direct_url.json"))
    assert provenance["vcs_info"]["commit_id"] == expected_revision, provenance
    files = [path for path in package.files or () if path.parts[0] == "design_mcp" and path.suffix != ".pyc"]
    for entry in files:
        source = subprocess.check_output(["git", "-C", str(checkout), "show", f"{expected_revision}:{entry}"])
        assert entry.locate().read_bytes() == source, str(entry)
    assert len(files) >= 49, len(files)
    print(f"PASS exact package content — {len(files)} files at {expected_revision}")


async def replay(scratch: Path) -> None:
    briefs = json.loads(Path(__file__).with_name("briefs.json").read_text())
    executable = Path(sys.executable).with_name("design-mcp")
    env = {"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"}
    with TemporaryDirectory(dir=scratch) as empty:
        transport = StdioTransport(command=str(executable), args=["serve"], cwd=empty, env=env)
        async with Client(transport, timeout=20) as client:
            for case in briefs:
                result = await client.call_tool("direct", {"brief": case["brief"]})
                assert not result.is_error and result.structured_content, case["id"]
                direction = result.structured_content["direction"]
                expected = case["expect"]
                if expected == "consultation-excluded":
                    assert direction["id"] != "direct-consultation", (case["id"], direction["id"])
                else:
                    assert direction["id"] == expected, (case["id"], direction["id"])
                if expected == "direct-consultation":
                    instruction = direction["action"]["instruction"].lower()
                    for channel in ("text", "email", "call"):
                        assert channel in instruction, (case["id"], channel)
                print(f"PASS installed route — {case['id']} → {direction['id']}")
    print(f"PASS clean consultation replay — {len(briefs)}/{len(briefs)}")


if __name__ == "__main__":
    checkout, scratch, revision = sys.argv[1:]
    verify_package(Path(checkout), revision)
    asyncio.run(replay(Path(scratch)))
