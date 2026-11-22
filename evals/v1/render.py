"""Render benchmark HTML through Playwriter MCP in an isolated Chrome process."""

import argparse
import asyncio
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import socket
import subprocess
from threading import Thread
import time
from urllib.request import urlopen
from urllib.parse import urlsplit

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from generate import sha256

VIEWPORTS = ((1440, 900), (390, 844))
REGIONS_JS = Path(__file__).with_name("visible-regions.js").read_text(encoding="utf-8")
CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com data:; "
    "img-src data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/index.html":
            self.send_error(404)
            return
        body = self.server.fixture
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


@contextmanager
def fixture_server():
    with ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler) as server:
        server.fixture = b""
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield server
        finally:
            server.shutdown()
            worker.join()


@contextmanager
def child(args, log, env=None):
    with log.open("wb") as stream:
        process = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT, env=env)
        try:
            yield process
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def wait_ready(process, probe, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Owned process exited with status {process.returncode}")
        try:
            return probe()
        except (ValueError, OSError):
            time.sleep(0.15)
    raise TimeoutError("Timed out waiting for an isolated local service")


def query_json(url):
    with urlopen(url, timeout=1) as reply:
        return json.load(reply)


def dynamic_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def result_text(result):
    return "\n".join(block.text for block in result.content if block.type == "text")


async def execute(client, code):
    return result_text(await client.call_tool("execute", {"code": code, "timeout": 15000}))


async def capture(client, cell, width, height, url):
    path = cell / f"{width}.png"
    await execute(client, """
      state.page = await context.newPage();
      state.pageErrors = [];
      state.page.on('pageerror', error => state.pageErrors.push(String(error).slice(0, 240)));
    """)
    try:
        await execute(client, f"""
          await state.page.setViewportSize({{width:{width}, height:{height}}});
          await state.page.emulateMedia({{reducedMotion:'reduce'}});
          await state.page.addInitScript(() => {{localStorage.clear(); sessionStorage.clear();}});
          await state.page.goto({json.dumps(url)}, {{waitUntil:'load', timeout:12000}});
        """)
        response = await execute(client, f"""
          const metrics = await state.page.evaluate(async () => {{
            await document.fonts.ready;
            const root = document.documentElement;
            const h1 = document.querySelector('h1');
            return {{
              viewport: innerWidth, width: root.scrollWidth, height: root.scrollHeight,
              title: document.title, h1: h1?.textContent.trim(),
              loadedFonts: [...new Set([...document.fonts].filter(f=>f.status==='loaded').map(f=>f.family))],
              language: root.lang,
              reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches
            }};
          }});
          await state.page.screenshot({{path:{json.dumps(str(path))}, animations:'disabled'}});
          const accessibility = await state.page.locator('body').ariaSnapshot();
          const regions = await state.page.evaluate({REGIONS_JS});
          console.log('EVAL_RESULT ' + JSON.stringify({{...metrics, pageErrors:state.pageErrors,
            accessibility:accessibility.slice(0,1400), regions}}));
        """)
        line = next((s for s in response.splitlines() if "EVAL_RESULT " in s), None)
        if line is None or not path.exists():
            raise RuntimeError(f"Playwriter produced no capture receipt: {response[-1000:]}")
        payload = line.split("EVAL_RESULT ", 1)[1]
        metrics, _ = json.JSONDecoder().raw_decode(payload)
        metrics.update(status="rendered", sha256=sha256(path.read_bytes()))
        return metrics
    finally:
        await execute(client, "await state.page.close();")


async def render_all(args, chrome, server, env, web_socket):
    transport = StdioTransport(command=str(args.playwriter), args=[], env=env, cwd=str(args.scratch))
    async with Client(transport, timeout=40) as client:
        tools = {tool.name for tool in await client.list_tools()}
        assert {"session_new", "execute"} <= tools, tools
        session = await client.call_tool("session_new", {"direct": web_socket})
        if not re.search(r"Session .+ created", result_text(session)):
            raise RuntimeError(f"Cannot open the isolated Playwriter session: {result_text(session)}")
        url = args.public_reference or f"http://127.0.0.1:{server.server_port}/index.html"
        source = urlsplit(url)
        same_origin = f"{source.scheme}://{source.netloc}" if args.public_reference else None
        await execute(client, f"""
          await context.route('**/*', route => {{
            const request = route.request();
            const origin = new URL(request.url()).origin;
            const font = (origin === 'https://fonts.googleapis.com' && request.resourceType() === 'stylesheet') ||
              (origin === 'https://fonts.gstatic.com' && request.resourceType() === 'font');
            if (request.method() === 'GET' && (request.url() === {json.dumps(url)} || font || origin === {json.dumps(same_origin)})) {{
              return route.continue();
            }}
            return route.abort();
          }});
        """)
        for template in sorted(args.cells.glob("*/*/index.html")):
            if args.case and template.parent.parent.name not in args.case:
                continue
            cell = template.parent
            receipt = cell / "render.json"
            if receipt.exists():
                continue
            server.fixture = template.read_bytes()
            captures = {}
            for width, height in VIEWPORTS:
                try:
                    captures[width] = await capture(client, cell, width, height, url)
                except (RuntimeError, ValueError, TimeoutError) as error:
                    captures[width] = {"status": "render-error", "message": str(error)}
            record = {"renderer": args.renderer, "browser": chrome, "input_sha256": sha256(server.fixture), "source_url": args.public_reference,
                      "captures": captures}
            receipt.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            print(template.parent.relative_to(args.cells),
                  {width: value["status"] for width, value in captures.items()}, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cells", type=lambda path: Path(path).resolve(), required=True)
    p.add_argument("--playwriter", type=lambda path: Path(path).absolute(), required=True)
    p.add_argument("--chrome", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    p.add_argument("--scratch", type=lambda path: Path(path).resolve(), required=True)
    p.add_argument("--case", action="append")
    p.add_argument("--public-reference", choices=("https://designsystem.digital.gov/templates/form-templates/address-form/",))
    args = p.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=False)
    profile = args.scratch / "profile"
    isolated_home = args.scratch / "home"
    isolated_home.mkdir()
    args.renderer = subprocess.check_output([args.playwriter, "--version"], text=True).strip()
    relay_port = dynamic_port()
    env = {k: v for k, v in os.environ.items() if not k.startswith("PLAYWRITER_")}
    env.update(HOME=str(isolated_home), PLAYWRITER_PORT=str(relay_port))
    chrome_args = [
        args.chrome, "--headless", "--disable-extensions", "--disable-sync", "--disable-background-networking",
        "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
        "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "about:blank",
    ]
    relay_args = [args.playwriter, "serve", "--host", "127.0.0.1"]
    with child(chrome_args, args.scratch / "chrome.log") as chrome:
        cdp_port = wait_ready(chrome, lambda: int((profile / "DevToolsActivePort").read_text().splitlines()[0]))
        version = wait_ready(chrome, lambda: query_json(f"http://127.0.0.1:{cdp_port}/json/version"))
        with child(relay_args, args.scratch / "relay.log", env=env) as relay, fixture_server() as server:
            def relay_ready():
                with socket.create_connection(("127.0.0.1", relay_port), timeout=1):
                    return True

            wait_ready(relay, relay_ready)
            asyncio.run(render_all(args, version["Browser"], server, env, version["webSocketDebuggerUrl"]))


if __name__ == "__main__":
    main()
