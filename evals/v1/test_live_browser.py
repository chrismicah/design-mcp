"""Exercise the evaluator MCP through a fake Playwriter transport."""

import asyncio
import base64
import hashlib
import json
from pathlib import Path
import re

from fastmcp import Client, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools import ToolResult
from mcp.types import ImageContent, TextContent
import pytest
import pytest_asyncio

from live_browser import LiveBrowser, create_server

URL = "http://127.0.0.1:49100/view.html"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO"
                       "+V/5kAAAAASUVORK5CYII=")
PREVIEW = ImageContent(type="image", data="/9g=", mimeType="image/jpeg")


class FakePlaywriter:
    def __init__(self):
        self.server = FastMCP("Fake Playwriter")
        self.calls = []
        self.keys = []
        self.destination = None
        self.bad_preview = False
        self.server.tool(self.session_new)
        self.server.tool(self.execute)

    async def session_new(self, direct: str) -> str:
        self.calls.append(("session_new", direct))
        return "Session 7 created. It is now the default session."

    async def execute(self, code: str, session: str, timeout: int) -> ToolResult:
        assert session == "7" and timeout == 18000
        self.calls.append(("execute", code))
        await asyncio.sleep(0)
        url = json.JSONDecoder().raw_decode(code.split("const url = ", 1)[1])[0]
        if "await page.goto" in code:
            assert "state.view?.close()" in code and "browser.newContext" in code
            assert "maxRedirects:0" in code and "state.view.route(" in code
            self.viewport = json.JSONDecoder().raw_decode(code.split("const viewport = ", 1)[1])[0]
            self.destination, self.value = url, ""
        elif self.destination != url:
            assert "page.url() !== url" in code
            raise ToolError("Unexpected fixture state")

        key = re.search(r"await page\.keyboard\.press\((.*)\);", code)
        text = re.search(r"await page\.keyboard\.insertText\((.*)\);", code)
        if key or text:
            assert code.index("guard();") < code.index("await page.keyboard.")
            if key:
                self.keys.append(json.loads(key[1]))
            else:
                self.value = json.loads(text[1])
        screenshot = re.search(r"await page\.screenshot\(\{path:(.+?), type:'png'", code)
        blocks = []
        if screenshot:
            Path(json.loads(screenshot[1])).write_bytes(PNG)
            if "resizeImageForAgent({input:png, maxDimension:1000" in code and not self.bad_preview:
                blocks.append(PREVIEW)
        observation = {"url": self.destination, **self.viewport, "layout_width": 412,
                       "focus": {"tag": "input" if self.keys else "body", "visible": bool(self.keys)}}
        if not screenshot:
            assert "ariaSnapshot" in code and "[AX truncated]" in code
            observation["ax"] = f'textbox: {self.value}'
        receipt = "[return value] LIVE_VIEW " + json.dumps(observation)
        return ToolResult(content=[TextContent(type="text", text=receipt), *blocks])


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return {"playwriter": "/local/playwriter", "relay_port": 49200,
            "cdp": "ws://127.0.0.1:49300/devtools/browser/test",
            "pages": {"A": URL, "B": "http://localhost:49100/other.html"},
            "evidence_dir": tmp_path / "evidence"}


@pytest_asyncio.fixture
async def connected(config):
    browser = LiveBrowser(config)
    playwriter = FakePlaywriter()
    async with Client(playwriter.server) as relay, Client(create_server(browser)) as judge:
        await browser.connect(relay)
        yield judge, playwriter, browser.evidence


@pytest.mark.asyncio
async def test_tool_schema_and_observed_operations(connected):
    judge, relay, evidence = connected
    schemas = {tool.name: tool.input_schema for tool in await judge.list_tools()}
    assert set(schemas) == {"open_view", "act", "capture"}
    assert schemas["open_view"]["properties"]["width"]["enum"] == [1440, 390]
    assert schemas["act"]["properties"]["action"]["enum"] == ["key", "text", "reload"]
    assert schemas["capture"]["required"] == ["label"]

    opened = (await judge.call_tool("open_view", {"page_id": "A", "width": 390})).data
    assert (opened["url"], opened["width"], opened["height"], opened["layout_width"]) == (URL, 390, 844, 412)
    tab = (await judge.call_tool("act", {"action": "key", "value": "Tab"})).data
    assert tab["focus"]["tag"] == "input" and relay.keys == ["Tab"]
    text = 'Clear "glass"'
    await judge.call_tool("act", {"action": "text", "value": text})
    reloaded = (await judge.call_tool("act", {"action": "reload"})).data
    assert reloaded["ax"] == f"textbox: {text}"
    assert "await page.reload" in relay.calls[-1][1] and "browser.newContext" not in relay.calls[-1][1]

    response = await judge.call_tool("capture", {"label": "A-390-before"})
    metadata = json.loads(response.content[0].text)
    assert response.content[1] == PREVIEW
    assert metadata["focus"] == tab["focus"] and metadata["layout_width"] == 412
    assert (evidence / metadata["path"]).read_bytes() == PNG
    assert metadata["sha256"] == hashlib.sha256(PNG).hexdigest()
    audit = (evidence / "audit.jsonl").read_text()
    rows = [json.loads(line) for line in audit.splitlines()]
    assert [row["op"] for row in rows] == ["open_view", "act", "act", "act", "capture"]
    assert rows[-1]["sha256"] == metadata["sha256"] and rows[-1]["path"] == metadata["path"]
    assert PREVIEW.data not in audit and base64.b64encode(PNG).decode() not in audit

    desktop = (await judge.call_tool("open_view", {"page_id": "B", "width": 1440})).data
    assert (desktop["width"], desktop["height"], desktop["ax"]) == (1440, 900, "textbox: ")
    assert [op for op, _ in relay.calls].count("session_new") == 1


@pytest.mark.parametrize("url", [
    "https://example.org/view", "http://localhost@example.org/view", "http://localhost:81/#other",
    "http://127.0.0.1\\@example.org/view", "//127.0.0.1:81/view", "file:///tmp/view.html",
    "http://[::1]example.org/view",
])
def test_disallowed_fixture_urls(config, url):
    config["pages"]["A"] = url
    with pytest.raises(ValueError):
        LiveBrowser(config)
    assert not config["evidence_dir"].exists()


def test_constructor_pins_relay_and_rejects_unsafe_config(config):
    for change in (
        {"cdp": "ws://example.org/remote"}, {"relay_port": True}, {"pages": {"../A": URL}},
        {"original_capture": "true"},
        {"evidence_dir": config["evidence_dir"].parent.parent / "outside"},
    ):
        with pytest.raises(ValueError):
            LiveBrowser({**config, **change})
    browser = LiveBrowser(config)
    assert browser.transport.command == "/local/playwriter"
    assert browser.transport.env == {"PLAYWRITER_PORT": "49200", "PLAYWRITER_HOST": "http://127.0.0.1:49200"}


@pytest.mark.asyncio
async def test_release_capture_returns_the_archived_png(config):
    browser = LiveBrowser({**config, "original_capture": True})
    playwriter = FakePlaywriter()
    async with Client(playwriter.server) as relay, Client(create_server(browser)) as judge:
        await browser.connect(relay)
        await judge.call_tool("open_view", {"page_id": "A", "width": 1440})
        response = await judge.call_tool("capture", {"label": "release"})
    metadata = json.loads(response.content[0].text)
    png = base64.b64decode(response.content[1].data)
    assert response.content[1].mime_type == "image/png"
    assert png == (browser.evidence / metadata["path"]).read_bytes() == PNG
    assert metadata["sha256"] == hashlib.sha256(png).hexdigest()
    assert "resizeImageForAgent" not in playwriter.calls[-1][1]


@pytest.mark.asyncio
async def test_invalid_inputs_have_no_browser_call(connected):
    judge, relay, evidence = connected
    await judge.call_tool("open_view", {"page_id": "A", "width": 390})
    await judge.call_tool("capture", {"label": "first"})
    before = relay.calls[:]
    for tool, args in (
        ("open_view", {"page_id": "../A", "width": 390}),
        ("open_view", {"page_id": "unknown", "width": 390}),
        ("open_view", {"page_id": "A", "width": 800}),
        ("act", {"action": "key", "value": "Control+l"}),
        ("act", {"action": "key", "value": "Tab", "code": "location.reload()"}),
        ("act", {"action": "text", "value": "two\nlines"}),
        ("act", {"action": "text", "value": "x" * 257}),
        ("act", {"action": "reload", "value": URL}),
        ("capture", {"label": "../escape"}),
        ("capture", {"label": "first"}),
    ):
        assert (await judge.call_tool(tool, args, raise_on_error=False)).is_error
    assert relay.calls == before and relay.keys == []
    assert sorted(path.name for path in evidence.iterdir()) == ["audit.jsonl", "first.png"]


@pytest.mark.asyncio
async def test_browser_error_disarms_input_and_failed_capture_leaves_no_png(connected):
    judge, relay, evidence = connected
    await judge.call_tool("open_view", {"page_id": "A", "width": 390})
    relay.destination = "about:blank"
    key = {"action": "key", "value": "Tab"}
    with pytest.raises(ToolError, match="Browser operation failed"):
        await judge.call_tool("act", key)
    before = relay.calls[:]
    with pytest.raises(ToolError, match="Open a view first"):
        await judge.call_tool("act", key)
    assert relay.calls == before and relay.keys == []

    await judge.call_tool("open_view", {"page_id": "A", "width": 390})
    relay.bad_preview = True
    with pytest.raises(ToolError, match="Browser operation failed"):
        await judge.call_tool("capture", {"label": "failed"})
    assert [path.name for path in evidence.iterdir()] == ["audit.jsonl"]
    errors = [json.loads(row) for row in (evidence / "audit.jsonl").read_text().splitlines()][1::2]
    assert [row["status"] for row in errors] == ["error", "error"]


@pytest.mark.asyncio
async def test_concurrent_capture_label_writes_once(connected):
    judge, relay, evidence = connected
    await judge.call_tool("open_view", {"page_id": "A", "width": 390})
    results = await asyncio.gather(*(
        judge.call_tool("capture", {"label": "once"}, raise_on_error=False) for _ in range(2)
    ))
    assert sorted(result.is_error for result in results) == [False, True]
    assert len(relay.calls) == 3
    assert (evidence / "once.png").read_bytes() == PNG
