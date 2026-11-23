import base64
import hashlib
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from design_mcp.review import tool
from tests.test_review import board


ROOT = Path(__file__).resolve().parents[1]


def server_client(*args):
    transport = StdioTransport(command=sys.executable, args=["-m", "design_mcp.cli", "serve", *args],
                               env={"DESIGN_MCP_SURFACE": "v2", "PYTHONPATH": str(ROOT)})
    return Client(transport, timeout=15)


@pytest.mark.asyncio
async def test_opt_in_and_rejections_over_stdio():
    async with server_client() as client:
        assert {item.name for item in await client.list_tools()} == {"direct", "react", "check", "get_component_pattern"}

    async with server_client("--review") as client:
        tools = {item.name: item for item in await client.list_tools()}
        assert set(tools) == {"direct", "react", "check", "get_component_pattern", "review_page"}
        annotations = tools["review_page"].annotations
        assert annotations.read_only_hint and annotations.open_world_hint and not annotations.destructive_hint

        cases = (
            ("http://127.0.0.1:8765", "private-address"),
            ("https://public.example/path?token=regression-secret", "credentials-in-url"),
        )
        for url, code in cases:
            result = await client.call_tool("review_page", {"url": url}, raise_on_error=False)
            assert result.is_error
            assert result.structured_content["code"] == code
            assert all(block.type == "text" for block in result.content)
            assert "regression-secret" not in str(result.structured_content)
            assert all("regression-secret" not in block.text for block in result.content)


@pytest.mark.asyncio
async def test_review_returns_actual_image_and_names_scope(monkeypatch):
    bundle = board(source="pasted-url")

    def capture(url, *, viewport):
        assert url == "https://boards.example/rooms"
        assert viewport == (390, 844)
        return bundle

    monkeypatch.setattr(tool, "capture_pasted_url", capture)
    result = await tool.review_page("https://boards.example/rooms", viewport="mobile")
    assert not result.is_error
    image = result.content[1]
    assert image.type == "image" and image.mime_type == "image/png"
    assert image.data == bundle["frames"][0]["screenshot"]["data"]
    facts = result.structured_content
    digest = hashlib.sha256(base64.b64decode(image.data)).hexdigest()
    assert facts["image"] == {"resolution": "original", "sha256": digest, "original_png_sha256": digest}
    assert facts["interaction"] == "initial-view-only"
    assert facts["viewport"]["width"] == 390
    assert facts["regions"]
    assert facts["local_findings"]


@pytest.mark.asyncio
async def test_oversized_capture_without_thumbnail_returns_actionable_error(monkeypatch):
    monkeypatch.setattr(tool, "_MAX_IMAGE_BASE64_BYTES", 1)
    monkeypatch.setattr(tool, "capture_pasted_url", lambda *_args, **_kwargs: board(source="pasted-url"))
    result = await tool.review_page("https://boards.example/rooms")
    assert result.is_error
    assert result.structured_content["code"] == "image-too-large"
    assert "mobile viewport" in result.structured_content["message"]
