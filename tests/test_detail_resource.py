from importlib.resources import files

import pytest
from fastmcp import Client

from design_mcp.detail_resource import DETAIL_RESOURCE_URI, image_detail_source
from design_mcp.server import mcp


@pytest.mark.asyncio
async def test_disclosure_resource_serves_the_bundled_source():
    async with Client(mcp) as client:
        resources = await client.list_resources()
        example = next(item for item in resources if str(item.uri) == DETAIL_RESOURCE_URI)
        assert example.mimeType == "text/plain"
        text, = await client.read_resource(DETAIL_RESOURCE_URI)
        assert text.text == image_detail_source() == (
            files("design_mcp") / "data" / "detail-disclosure.html"
        ).read_text(encoding="utf-8")
        assert "aria-controls" in text.text and "@media (prefers-reduced-motion:reduce)" in text.text
