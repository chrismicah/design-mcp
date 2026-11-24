"""Check the social design trial and its unchanged controls over MCP stdio."""

import asyncio
import json
from pathlib import Path
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXPECTED = {
    "social-lighting": ("ground-plane", "cue-stage"),
    "social-river": ("margin-front", "level-cross-section"),
    "social-permit": ("grouped-fieldsets", "grouped-fieldsets"),
}


def cases(path):
    return json.loads(path.read_text(encoding="utf-8"))


def server(args):
    return Client(StdioTransport(command=sys.executable, args=args, cwd=str(ROOT),
                                 env={"PYTHONPATH": str(ROOT), "DESIGN_MCP_SURFACE": "v2",
                                      "FASTMCP_SHOW_SERVER_BANNER": "false"}), timeout=10)


async def preflight():
    creative = cases(HERE / "tasks.json")
    frozen = cases(ROOT / "evals/v1/tasks.json")
    changes = {}
    async with server(["-m", "design_mcp.cli", "serve"]) as control, \
               server([str(HERE / "serve.py"), "serve"]) as trial:
        control_tools, trial_tools = await asyncio.gather(control.list_tools(), trial.list_tools())
        assert control_tools == trial_tools
        for case in [*creative, *frozen]:
            args = {"brief": case["brief"]}
            plain, added = await asyncio.gather(control.call_tool("direct", args), trial.call_tool("direct", args))
            first, second = plain.structured_content, added.structured_content
            case_id = case["id"]
            if case_id in EXPECTED:
                ids = first["direction"]["id"], second["direction"]["id"]
                assert ids == EXPECTED[case_id], (case_id, ids)
                if ids[0] == ids[1]:
                    assert first == second
                changes[case_id] = ids
            else:
                assert first == second, case_id
    return {"creative_and_form_routes": changes, "unchanged_frozen_replies": len(frozen),
            "model_calls": 0, "live_visual_verdict": "pending"}


if __name__ == "__main__":
    print(json.dumps(asyncio.run(preflight()), indent=2))
