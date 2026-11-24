"""Check the installed review tool over stdio against the public USWDS fixture."""

import argparse
import asyncio
from base64 import b64decode
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack
from time import perf_counter

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


ADDRESS_FORM = "https://designsystem.digital.gov/templates/form-templates/address-form/"
MISSING_PAGE = "https://designsystem.digital.gov/components/address-form/"


async def verify_image(client, output, viewport, expected_size):
    start = perf_counter()
    result = await client.call_tool("review_page", {"url": ADDRESS_FORM, "viewport": viewport})
    elapsed_ms = round((perf_counter() - start) * 1000)
    facts = result.structured_content
    assert not result.is_error and facts["ok"]
    text, image = result.content
    assert text.type == "text" and json.loads(text.text) == facts
    assert image.type == "image" and image.mime_type == "image/png"
    pixels = b64decode(image.data, validate=True)
    assert pixels.startswith(b"\x89PNG\r\n\x1a\n") and pixels[12:16] == b"IHDR"
    assert unpack(">II", pixels[16:24]) == expected_size
    digest = sha256(pixels).hexdigest()
    assert facts["image"] == {"resolution": "original", "sha256": digest, "original_png_sha256": digest}
    assert facts["capture"]["url"] == ADDRESS_FORM and facts["interaction"] == "initial-view-only"
    assert facts["masked"]["field"] > 0
    assert any(region["name"] == "Street address" and region["masked"] for region in facts["regions"])
    file = f"mcp-{viewport}.png"
    (output / file).write_bytes(pixels)
    return {"file": file, "sha256": digest, "size": expected_size, "milliseconds": elapsed_ms,
            "masked": facts["masked"]}


async def verify_error(client, url, code, message_contains=None):
    result = await client.call_tool("review_page", {"url": url}, raise_on_error=False)
    facts = result.structured_content
    assert result.is_error and facts["ok"] is False and facts["code"] == code, facts
    assert all(block.type == "text" for block in result.content)
    if message_contains:
        assert message_contains in facts["message"], facts
    return facts


async def verify(executable, output):
    output.mkdir()
    start = perf_counter()
    transport = StdioTransport(command=str(executable), args=["serve", "--review"],
                               env={"DESIGN_MCP_SURFACE": "v2", "FASTMCP_SHOW_SERVER_BANNER": "false"})
    async with Client(transport, timeout=45) as client:
        names = sorted(tool.name for tool in await client.list_tools())
        assert names == ["check", "direct", "react", "review_page"], names
        cold_list_ms = round((perf_counter() - start) * 1000)
        desktop = await verify_image(client, output, "desktop", (1440, 900))
        missing = await verify_error(client, MISSING_PAGE, "capture-failed", "HTTP 404")
        unsupported = await verify_error(client, "file:///design-mcp-smoke", "unsupported-url")
        mobile = await verify_image(client, output, "mobile", (390, 844))
        result = await client.call_tool("direct", {"brief": "Build a mobile ticket screen for a train rider."})
        assert result.structured_content["direction"]["id"] == "platform-sign"
    receipt = {"tools": names, "cold_list_ms": cold_list_ms, "url": ADDRESS_FORM,
               "captures": {"desktop": desktop, "mobile": mobile},
               "failures": {"missing_page": missing, "unsupported": unsupported}, "recovered": True}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=lambda value: Path(value).resolve(strict=True))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    asyncio.run(verify(args.executable, args.output))
