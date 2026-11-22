from fastmcp import Client, FastMCP
import pytest

from design_library_mode import create_server
from generate import parse_cell


@pytest.mark.asyncio
async def test_both_adapters_have_the_same_schema_and_only_forward_their_mode():
    library = FastMCP("Fixture library")
    observed = []

    @library.tool
    def search_designs(query: str, mode: str, limit: int) -> list[dict]:
        observed.append((query, mode, limit))
        return [{"id": "reference"}]

    @library.tool
    def get_design(id: str) -> dict:
        return {"id": id, "license": "MIT"}

    catalogs = []
    async with Client(library) as upstream:
        for mode in ("keyword", "hybrid"):
            async with Client(create_server(upstream, mode)) as adapter:
                catalogs.append([tool.model_dump(mode="json") for tool in await adapter.list_tools()])
                search = await adapter.call_tool("search_designs", {"query": "shop"})
                assert search.structured_content == {"retrieval_mode": mode, "results": [{"id": "reference"}]}
                detail = await adapter.call_tool("get_design", {"id": "reference"})
                assert detail.structured_content == {"id": "reference", "license": "MIT"}
                override = await adapter.call_tool("search_designs", {"query": "shop", "mode": "other"}, raise_on_error=False)
                assert override.is_error
    assert catalogs[0] == catalogs[1]
    assert observed == [("shop", "keyword", 3), ("shop", "hybrid", 3)]


@pytest.mark.parametrize("mode, rows, detail, expected", [
    ("hybrid", [{"id": "ref"}], "ref", "passed"),
    ("keyword", [{"id": "ref"}], "ref", "design-library-mode-mismatch"),
    ("hybrid", [], "ref", "design-library-result-unread"),
    ("hybrid", [{"id": "ref"}], "unrelated", "design-library-result-unread"),
])
def test_generation_requires_a_search_hit_and_matching_detail(mode, rows, detail, expected):
    def call(tool, arguments, content):
        return {"type": "item.completed", "item": {
            "type": "mcp_tool_call", "server": "design-library", "tool": tool, "status": "completed",
            "arguments": arguments, "result": {"structured_content": content},
        }}

    trace = [call("search_designs", {"query": "shop"}, {"retrieval_mode": mode, "results": rows}),
             call("get_design", {"id": detail}, {"id": detail, "license": "MIT"}),
             {"type": "item.completed", "item": {"type": "agent_message", "text": "```html\n<body>Shop</body>\n```"}},
             {"type": "turn.completed", "usage": {"input_tokens": 150}}]
    parsed, html = parse_cell(trace, expect_mcp=True, server_name="design-library",
                              expected_tool=["search_designs", "get_design"], design_library_mode="hybrid")
    assert parsed["status"] == expected
    assert parsed["read_design_library_ids"] == (["ref"] if expected == "passed" else [])
    assert html == "<body>Shop</body>\n"
