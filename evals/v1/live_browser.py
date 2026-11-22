"""Serve bounded browser controls for an independent live evaluator over stdio."""

import argparse
import asyncio
import base64
from ipaddress import ip_address
import json
from pathlib import Path
import re
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from fastmcp import Client, FastMCP
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError
from fastmcp.tools import ToolResult
from mcp.types import ImageContent, TextContent

from generate import sha256
from render import VIEWPORTS, result_text

KEYS = frozenset("Tab Shift+Tab Enter Space Backspace Escape ArrowUp ArrowDown "
                 "ArrowLeft ArrowRight ControlOrMeta+a".split())
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}")
RECEIPT = re.compile(r"^\[return value\] LIVE_VIEW (.+)$", re.MULTILINE)

# A fresh context starts with empty local and session storage. Its route also
# covers the first request of a popup and leaves other browser contexts alone.
OPEN = """
await state.view?.close();
state.view = await browser.newContext({viewport, serviceWorkers:'block', acceptDownloads:false});
const page = state.page = await state.view.newPage();
state.pageError = false;
page.on('pageerror', () => { state.pageError = true; });
page.on('framenavigated', frame => {
  if (frame === page.mainFrame() && frame.url() !== url) state.pageError = true;
});
await state.view.routeWebSocket('**/*', socket => socket.close());
await state.view.route('**/*', async route => {
  const request = route.request();
  try {
    const origin = new URL(request.url()).origin;
    const font = (origin === 'https://fonts.googleapis.com' && request.resourceType() === 'stylesheet') ||
                 (origin === 'https://fonts.gstatic.com' && request.resourceType() === 'font');
    const main = request.isNavigationRequest() && request.frame() === page.mainFrame();
    if (main && request.url() !== url) state.pageError = true;
    if (request.method() === 'GET' && ((main && request.url() === url) || font)) {
      // continue() would follow redirects without applying this allowlist again.
      const response = await route.fetch({maxRedirects:0, timeout:5000});
      if (response.ok()) return await route.fulfill({response});
    }
  } catch {
    // A navigation request can precede creation of its frame (e.g. a popup).
  }
  return route.abort();
});
if (!(await page.goto(url, {waitUntil:'load', timeout:8000}))?.ok())
  throw new Error('Fixture load failed');
await page.evaluate(() => Promise.race([
  document.fonts.ready.then(() => {}),
  new Promise(resolve => setTimeout(resolve, 2000))
]));
"""

GUARD = """
const guard = () => {
  if (page.isClosed() || page.url() !== url || state.pageError || state.view.pages().length !== 1)
    throw new Error('Unexpected fixture state');
};
const readView = () => {
  let el = document.activeElement;
  while (el?.shadowRoot?.activeElement) el = el.shadowRoot.activeElement;
  return {
    url: location.href, width: innerWidth, height: innerHeight,
    layout_width: document.documentElement.scrollWidth,
    focus: {
      tag: el?.localName ?? null,
      label: (el?.getAttribute('aria-label') || el?.labels?.[0]?.innerText ||
              (el !== document.body ? el?.innerText : '') || '').trim().slice(0,160),
      visible: el?.matches(':focus-visible') ?? false,
      embedded: el?.matches('iframe,frame,object,embed') ?? false,
      document_focused: document.hasFocus()
    }
  };
};
guard();
"""

OBSERVE = r"""
const observation = await page.evaluate(readView);
if (includeAX) {
  const ax = await page.locator('body').ariaSnapshot({timeout:2500});
  const marker = '\n[AX truncated]';
  observation.ax = ax.length > 1800 ? ax.slice(0, 1800 - marker.length) + marker : ax;
}
guard();
return 'LIVE_VIEW ' + JSON.stringify(observation);
"""

INPUT_GUARD = """
if ((await page.evaluate(readView)).focus.embedded) throw new Error('Focus is outside the fixture document');
guard();
"""


def loopback_url(url, schemes):
    parts = urlsplit(url)
    if (parts.scheme not in schemes
            or not re.fullmatch(r"(?:localhost|[0-9.]+|\[[a-f0-9:.]+\])(?::[0-9]+)?", parts.netloc, re.I)
            or parts.port == 0 or any(c.isspace() or not c.isprintable() or c in "#\\" for c in url)):
        raise ValueError("Use an absolute loopback URL without credentials or fragments")
    host = parts.hostname
    if host != "localhost":
        addr = ip_address(host)
        if not addr.is_loopback:
            raise ValueError("Use a loopback hostname or IP address")
        host = f"[{addr}]" if addr.version == 6 else str(addr)
    default_port = 443 if parts.scheme in {"https", "wss"} else 80
    netloc = f"{host}:{parts.port}" if parts.port not in {None, default_port} else host
    return urlunsplit((parts.scheme, netloc, parts.path or "/", parts.query, ""))


class LiveBrowser:
    def __init__(self, config):
        self.cdp = loopback_url(config["cdp"], {"ws", "wss"})
        self.pages = {key: loopback_url(url, {"http", "https"}) for key, url in config["pages"].items()}
        if not self.pages or any(not IDENTIFIER.fullmatch(key) for key in self.pages):
            raise ValueError("Use short neutral fixture IDs")
        port = config["relay_port"]
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Invalid relay port")
        self.original_capture = config.get("original_capture", False)
        if type(self.original_capture) is not bool:
            raise ValueError("original_capture must be a boolean")
        # An explicit relay URL prevents Playwriter from starting a missing relay.
        self.transport = StdioTransport(
            command=str(Path(config["playwriter"]).absolute()), args=[], keep_alive=False,
            env={"PLAYWRITER_PORT": str(port), "PLAYWRITER_HOST": f"http://127.0.0.1:{port}"})
        self.evidence = Path(config["evidence_dir"]).resolve()
        if Path.cwd() not in self.evidence.parents:
            raise ValueError("Evidence must be inside the launcher workspace")
        self.evidence.mkdir(parents=True, exist_ok=True)
        if any(self.evidence.iterdir()):
            raise ValueError("Evidence directory must be empty")
        self.active = None
        self.lock = asyncio.Lock()

    async def connect(self, client):
        self.client = client
        result = await client.call_tool("session_new", {"direct": self.cdp})
        session = re.search(r"^Session (\S+) created\b", result_text(result))
        if result.is_error or not session:
            raise RuntimeError("Cannot create the direct Playwriter session")
        self.session = session[1]

    def audit(self, row):
        with (self.evidence / "audit.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")

    async def run(self, row, page_id, code, path=None):
        url = self.pages[page_id]
        inputs = f"const url = {json.dumps(url)}, includeAX = {json.dumps(path is None)};\n"
        self.active = None
        try:
            result = await self.client.call_tool("execute", {
                "session": self.session, "timeout": 18000,
                "code": inputs + code + OBSERVE,
            })
            receipt = RECEIPT.search(result_text(result))
            if result.is_error or not receipt:
                raise ValueError("Missing live observation")
            observation = json.loads(receipt[1])
            if observation["url"] != url:
                raise ValueError("Unexpected destination")
            record = {**row, "page_id": page_id, "observation": observation}
            output = observation
            if path is not None:
                images = [block for block in result.content if block.type == "image"]
                png = path.with_suffix(".pending").read_bytes()
                if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise ValueError("Missing screenshot evidence")
                if self.original_capture:
                    image = ImageContent(type="image", data=base64.b64encode(png).decode("ascii"),
                                         mimeType="image/png")
                elif len(images) == 1:
                    image = images[0]
                else:
                    raise ValueError("Missing preview image")
                record.update(path=path.name, sha256=sha256(png))
                metadata = {**observation, "path": path.name, "sha256": record["sha256"]}
                output = ToolResult(content=[TextContent(type="text", text=json.dumps(metadata)), image])
                path.with_suffix(".pending").replace(path)
            self.audit(record)
        except Exception:
            if path is not None:
                path.with_suffix(".pending").unlink(missing_ok=True)
            self.audit({**row, "page_id": page_id, "status": "error"})
            raise ToolError("Browser operation failed. Open a fresh view.") from None
        self.active = page_id
        return output

    async def open_view(self, page_id: str, width: Literal[1440, 390]) -> dict:
        """Open a fixture by ID at desktop or mobile width."""
        if page_id not in self.pages or width not in dict(VIEWPORTS):
            raise ToolError("Choose a known fixture ID and width 1440 or 390")
        viewport = json.dumps({"width": width, "height": dict(VIEWPORTS)[width]})
        async with self.lock:
            return await self.run({"op": "open_view", "width": width}, page_id,
                                  f"const viewport = {viewport};\n" + OPEN + GUARD)

    async def act(self, action: Literal["key", "text", "reload"], value: str | None = None) -> dict:
        """Insert text, reload, or press Tab, Shift+Tab, Enter, Space, Backspace, Escape, an Arrow key, or ControlOrMeta+a."""
        if action == "key" and value in KEYS:
            command = INPUT_GUARD + f"await page.keyboard.press({json.dumps(value)});"
        elif action == "text" and value and len(value) <= 256 and value.isprintable():
            command = INPUT_GUARD + f"await page.keyboard.insertText({json.dumps(value)});"
        elif action == "reload" and value is None:
            command = ("if (!(await page.reload({waitUntil:'load', timeout:8000}))?.ok()) "
                       "throw new Error('Fixture reload failed');")
        else:
            raise ToolError("Choose an allowed key, 1–256 printable characters, or reload without a value")
        async with self.lock:
            if self.active is None:
                raise ToolError("Open a view first")
            return await self.run({"op": "act", "action": action, "value": value}, self.active,
                                  "const page = state.page;\n" + GUARD + command + "\n")

    async def capture(self, label: str) -> ToolResult:
        """Save a PNG and return a screenshot with live metadata."""
        if not IDENTIFIER.fullmatch(label):
            raise ToolError("Use a short alphanumeric capture label, with optional hyphens or underscores")
        path = self.evidence / f"{label}.png"
        async with self.lock:
            if path.exists() or path.is_symlink():
                raise ToolError("Capture label already used")
            if self.active is None:
                raise ToolError("Open a view first")
            code = f"""
const png = await page.screenshot({{path:{json.dumps(str(path.with_suffix(".pending")))}, type:'png', timeout:5000}});
"""
            if not self.original_capture:
                code += "await resizeImageForAgent({input:png, maxDimension:1000, format:'jpeg', quality:75});\n"
            return await self.run({"op": "capture", "label": label}, self.active,
                                  "const page = state.page;\n" + GUARD + code, path)


def create_server(browser):
    server = FastMCP("Live browser", strict_input_validation=True)
    server.tool(browser.open_view)
    server.tool(browser.act)
    server.tool(browser.capture)
    return server


async def serve(browser):
    async with Client(browser.transport, timeout=24) as client:
        await browser.connect(client)
        try:
            await create_server(browser).run_async(transport="stdio", show_banner=False)
        finally:
            try:
                await client.call_tool("execute", {
                    "session": browser.session, "code": "await state.view?.close();", "timeout": 5000,
                }, raise_on_error=False)
            finally:
                await client.call_tool("session_delete", {"session": browser.session}, raise_on_error=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    asyncio.run(serve(LiveBrowser(json.loads(parser.parse_args().config.read_text(encoding="utf-8")))))
