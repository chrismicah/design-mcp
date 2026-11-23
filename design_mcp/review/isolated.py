"""Capture a pasted public page in a separate, cookie-free Chrome through Playwriter.

This follows evals/v1/render.py, the renderer the benchmark already uses: an owned headless Chrome with
a new empty profile, an owned Playwriter relay and one stdio MCP session. The person's own browser
profile, cookies and extensions are never involved, and the page under review is only read.

The address rules live in address.py. The browser starts with a fresh profile for each capture.
"""

import asyncio
import base64
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

from .address import public_target
from .evidence import MAX_REGIONS, SCHEMA, EvidenceError
from .network import public_proxy
from .pipeline import _ms

VIEWPORTS = ((1440, 900), (390, 844))
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
COLLECTOR = Path(__file__).with_name("extension") / "collector.js"
SESSION_SECONDS = 120


class CaptureError(RuntimeError):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


# The proxy checks the resolved connection destination, including redirect targets.
_ROUTE_JS = r"""
await context.route('**/*', route => {
  let target;
  try { target = new URL(route.request().url()); } catch (error) { return route.abort(); }
  if (!/^https?:$/.test(target.protocol)) return route.abort();
  return route.continue();
});
"""

_OPEN_JS = r"""
state.page = await context.newPage();
await state.page.setViewportSize({width: __WIDTH__, height: __HEIGHT__});
await state.page.emulateMedia({reducedMotion: 'reduce'});
const started = Date.now();
await state.page.goto(__URL__, {waitUntil: 'load', timeout: 20000});
console.log('REVIEW_LOAD ' + (Date.now() - started));
"""

# Fields and frames are covered inside the separate browser before the screenshot is taken.
_COLLECT_JS = r"""
const started = Date.now();
const frame = await state.page.evaluate(__COLLECT__);
await state.page.evaluate(boxes => {
  for (const box of boxes) {
    const cover = document.createElement('div');
    cover.style.cssText = 'position:fixed;z-index:2147483647;background:#8a8f98;left:' + box.x * innerWidth +
      'px;top:' + box.y * innerHeight + 'px;width:' + box.width * innerWidth + 'px;height:' +
      box.height * innerHeight + 'px';
    document.documentElement.appendChild(cover);
  }
}, frame.masks.boxes.map(item => item.box));
frame.masks.applied = true;
await state.page.screenshot({path: __PATH__, animations: 'disabled'});
console.log('REVIEW_FRAME ' + JSON.stringify({frame, capture_ms: Date.now() - started}));
"""

_CLOSE_JS = "if (state.page) { await state.page.close(); state.page = null; }"


def collect_expression():
    """The collector as one JavaScript expression, the same source the extension injects."""
    source = COLLECTOR.read_text(encoding="utf-8")
    return "(() => {" + source + "\nreturn designMcpCollect({maxRegions: " + str(MAX_REGIONS) + "});})()"


def _marked(output, marker):
    lines = [line for line in output.splitlines() if marker in line]
    if not lines:
        raise RuntimeError(f"the separate browser returned no {marker.strip()} receipt: {output[-400:]}")
    value, _ = json.JSONDecoder().raw_decode(lines[-1].split(marker, 1)[1])
    return value


@contextmanager
def _child(args, log, env=None):
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


def _wait_ready(process, probe, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"an owned process exited with status {process.returncode}")
        try:
            return probe()
        except (ValueError, OSError):
            time.sleep(0.15)
    raise TimeoutError("timed out waiting for the separate browser")


def _free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


async def _drive(url, playwriter, env, scratch, web_socket):
    started = time.perf_counter()
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=str(playwriter), args=[], env=env, cwd=str(scratch))
    async with Client(transport, timeout=60) as client:
        def result_text(result):
            return "\n".join(block.text for block in result.content if block.type == "text")

        session = await client.call_tool("session_new", {"direct": web_socket})
        opened = result_text(session)
        match = re.search(r"^Session (\S+) created\b", opened, re.MULTILINE)
        if session.is_error or not match:
            raise RuntimeError(f"cannot open the separate Playwriter session: {opened[-400:]}")
        session_id = match[1]

        async def execute(code):
            result = await client.call_tool("execute", {"session": session_id, "code": code, "timeout": 30000})
            output = result_text(result)
            if result.is_error:
                raise RuntimeError(f"the separate Playwriter session stopped: {output[-400:]}")
            return output

        await execute(_ROUTE_JS)
        session_ready = time.perf_counter()
        collect = json.dumps(collect_expression())
        frames, loads, captures = [], [], []
        for width, height in VIEWPORTS:
            shot = scratch / f"{width}.png"
            try:
                loads.append(_marked(await execute(
                    _OPEN_JS.replace("__WIDTH__", str(width)).replace("__HEIGHT__", str(height))
                    .replace("__URL__", json.dumps(url))), "REVIEW_LOAD "))
                receipt = _marked(await execute(
                    _COLLECT_JS.replace("__COLLECT__", collect).replace("__PATH__", json.dumps(str(shot)))),
                    "REVIEW_FRAME ")
            finally:
                await execute(_CLOSE_JS)
            frame = receipt["frame"]
            frame["screenshot"] = {
                "media_type": "image/png",
                "data": base64.b64encode(shot.read_bytes()).decode("ascii"),
            }
            frames.append(frame)
            captures.append(receipt["capture_ms"])
    return {
        "schema": SCHEMA,
        "capture": {
            "source": "isolated-url",
            "url": url,
            "title": frames[0].get("title"),
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user_triggered": True,
        },
        "frames": frames,
        "timings_ms": {"page_load": max(loads), "capture": sum(captures)},
        "url_capture_ms": {
            "session_ready": _ms(started, session_ready),
            "viewports": [
                {"width": width, "page_load": load, "capture": capture}
                for (width, _), load, capture in zip(VIEWPORTS, loads, captures, strict=True)
            ],
        },
    }


def _browser_arguments(chrome, profile, proxy_port):
    return [
        str(chrome), "--headless", "--disable-extensions", "--disable-sync", "--disable-background-networking",
        "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
        f"--proxy-server=socks5://127.0.0.1:{proxy_port}", "--proxy-bypass-list=<-loopback>",
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1",
        "--disable-quic", "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    ]


async def _capture_browser(url, host, address, chrome, playwriter, scratch, resolve, *, viewport=VIEWPORTS[0]):
    started = time.perf_counter()
    profile, home = scratch / "profile", scratch / "home"
    home.mkdir()
    env = {key: value for key, value in os.environ.items() if not key.startswith("PLAYWRITER_")}
    env.update(HOME=str(home))
    async with public_proxy(host, address, resolve) as proxy_port:
        chrome_args = _browser_arguments(chrome, profile, proxy_port) + [
            "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "about:blank",
        ]
        chrome_started = time.perf_counter()
        with _child(chrome_args, scratch / "chrome.log") as browser:
            def devtools_port():
                lines = (profile / "DevToolsActivePort").read_text().splitlines()
                if not lines:
                    raise ValueError("the port is not written yet")
                return int(lines[0])

            port = await asyncio.to_thread(_wait_ready, browser, devtools_port)
            local_opener = build_opener(ProxyHandler({}))

            def version():
                with local_opener.open(f"http://127.0.0.1:{port}/json/version", timeout=1) as reply:
                    return json.load(reply)

            web_socket = (await asyncio.to_thread(_wait_ready, browser, version))["webSocketDebuggerUrl"]
            chrome_ready = time.perf_counter()
            if playwriter is None:
                from .direct_capture import capture_page

                bundle = await asyncio.wait_for(capture_page(url, web_socket, viewport), 30)
                relay_ready_at = chrome_ready
            else:
                relay_port = _free_port()
                env["PLAYWRITER_PORT"] = str(relay_port)
                with _child([str(playwriter), "serve", "--host", "127.0.0.1"], scratch / "relay.log", env=env) as relay:
                    def relay_ready():
                        with socket.create_connection(("127.0.0.1", relay_port), timeout=1):
                            return True

                    await asyncio.to_thread(_wait_ready, relay, relay_ready)
                    relay_ready_at = time.perf_counter()
                    bundle = await asyncio.wait_for(_drive(url, playwriter, env, scratch, web_socket), SESSION_SECONDS)
            drive_done = time.perf_counter()
    bundle["url_capture_ms"].update({
        "proxy_setup": _ms(started, chrome_started),
        "chrome_ready": _ms(chrome_started, chrome_ready),
        "relay_ready": _ms(chrome_ready, relay_ready_at),
        "drive": _ms(relay_ready_at, drive_done),
        "process_cleanup": _ms(drive_done, time.perf_counter()),
    })
    return bundle


def _capture(url, playwriter, chrome, resolve, *, direct_viewport=None):
    started = time.perf_counter()
    clean, host, address = public_target(url, resolve)
    if direct_viewport is None:
        playwriter = playwriter or shutil.which("playwriter")
        if not playwriter:
            raise CaptureError("Playwriter was not found on PATH. Install it or pass --playwriter with its path.")
        playwriter = Path(playwriter).expanduser().absolute()
        if not playwriter.is_file():
            raise CaptureError(f"No Playwriter executable at {playwriter}.")
    chrome = Path(chrome or (DEFAULT_CHROME if sys.platform == "darwin" else
                             shutil.which("google-chrome") or shutil.which("chromium") or DEFAULT_CHROME))
    if not chrome.is_file():
        if direct_viewport is not None:
            raise CaptureError("Chrome couldn't be found in its standard location. Open the page in Chrome and use Review this page.")
        raise CaptureError(f"No Chrome at {chrome}. Pass --chrome with its location.")
    scratch = Path(tempfile.mkdtemp(prefix="design-mcp-review-"))
    prepared = time.perf_counter()
    try:
        bundle = asyncio.run(_capture_browser(clean, host, address, chrome, playwriter, scratch, resolve,
                                              viewport=direct_viewport or VIEWPORTS[0]))
        browser_done = time.perf_counter()
    except (CaptureError, EvidenceError):
        raise
    except Exception as error:  # an external browser and tool: report one plain sentence, keep the cause
        if direct_viewport is not None:
            raise CaptureError("Chrome couldn't finish reviewing this page. Try again or review it from its open tab.") from error
        raise CaptureError(f"The page could not be captured in the separate browser: {error}") from error
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    bundle["url_capture_ms"].update({
        "prepare": _ms(started, prepared),
        "scratch_cleanup": _ms(browser_done, time.perf_counter()),
    })
    return bundle


def capture(url, playwriter=None, chrome=None, resolve=socket.getaddrinfo):
    """Capture both benchmark widths through Playwriter."""
    return _capture(url, playwriter, chrome, resolve)


def capture_pasted_url(url, *, viewport=VIEWPORTS[0]):
    """Capture one viewport in disposable Chrome without requiring Playwriter."""
    return _capture(url, None, None, socket.getaddrinfo, direct_viewport=viewport)
