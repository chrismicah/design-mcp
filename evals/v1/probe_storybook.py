"""Check that a pinned Storybook addon exposes usable docs for an owned fixture."""

import argparse
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import re
from time import monotonic

from fastmcp import Client


COMPONENT = "maintenance-disclosure"
STORY = "WithEscalation"
DESCRIPTION = "Reveals maintenance escalation instructions."
PROP = "Question shown in the disclosure control."
EXAMPLE = "Call dispatch if there is standing water."
MISSING = re.compile(r"not found|could not find|couldn't find|no (?:component|documentation|story)", re.I)


async def probe(endpoint):
    calls = {}
    async with Client(endpoint, timeout=30) as client:
        tools = await client.list_tools()

        async def lookup(label, name, args, expected=(), *, missing=False):
            started = monotonic()
            reply = await client.call_tool(name, args, raise_on_error=False)
            payload = json.dumps([part.model_dump(mode="json") for part in reply.content], sort_keys=True).encode()
            body = "\n".join(part.text for part in reply.content if part.type == "text")
            found = [phrase for phrase in expected if phrase in body]
            if missing:
                passed = bool(MISSING.search(body)) and not any(phrase in body for phrase in (DESCRIPTION, PROP, EXAMPLE))
            else:
                passed = not reply.is_error and len(found) == len(expected)
            calls[label] = {
                "tool": name,
                "arguments": args,
                "passed": passed,
                "is_error": reply.is_error,
                "matched": found,
                "milliseconds": round((monotonic() - started) * 1000),
                "payload_bytes": len(payload),
                "payload_sha256": sha256(payload).hexdigest(),
                "text": body[:10000],
            }

        await lookup("catalog", "docs-list", {}, (COMPONENT,))
        await lookup("component", "docs-show", {"id": COMPONENT}, (DESCRIPTION, PROP))
        await lookup("story", "docs-show-story", {"componentId": COMPONENT, "storyName": STORY}, (EXAMPLE,))
        await lookup("missing-component", "docs-show", {"id": "design-mcp-missing-component"}, missing=True)
        await lookup("missing-story", "docs-show-story", {
            "componentId": COMPONENT, "storyName": "DesignMcpMissingStory",
        }, missing=True)
    return {
        "scope": "Local Storybook development server with generated documentation for an owned React fixture. No visual scoring.",
        "tools": {tool.name: tool.model_dump(by_alias=True, exclude_none=True)["inputSchema"] for tool in tools},
        "calls": calls,
        "passed": all(row["passed"] for row in calls.values()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("endpoint")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(probe(args.endpoint))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print({name: row["passed"] for name, row in result["calls"].items()})
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
