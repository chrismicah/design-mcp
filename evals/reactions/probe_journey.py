"""Exercise the observer with synthetic fixtures through Chrome and Playwriter."""
import asyncio
import base64
from contextlib import ExitStack
from html import escape
import json
import os
from pathlib import Path
import socket
import struct
import sys

from fastmcp import Client

from live_review import child, dynamic_port, fixture_server, query_json, wait_ready
from audit_review import sha256
from cold_storage import audit_journey
from live_browser import LiveBrowser, create_server
from test_cold_storage import BOARD, CONTRACT

CHROME, PLAYWRITER, OUT = map(Path, sys.argv[1:])
OUT.mkdir()
os.chdir(OUT.parent)

FIXTURE = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font: 16px sans-serif; margin: 16px; }
li { margin: 0 0 8px; }
button { width: 170px; min-height: 44px; }
button:focus-visible { outline: 3px solid #44a; }
.deadline { position: relative; }
.screen { display: none; }
.cover .screen { display: block; position: absolute; inset: 0; background: white; }
</style>
<main>
<button type="button">Inspect</button>
<div id="due" class="deadline"><p>Next departure in nine minutes</p><span class="screen" aria-hidden="true"></span></div>
<ul>ROWS</ul>
</main>
<script>
let focused = false;
function toggle() {
  focused = !focused;
  const next = document.createElement('button');
  next.type = 'button';
  next.textContent = focused ? 'Restore queue' : 'Inspect';
  next.addEventListener('click', toggle);
  document.querySelector('button').replaceWith(next);
  next.focus();
  document.querySelectorAll('li').forEach((row, n) => row.hidden = n > 0 && focused);
  document.querySelector('#due').classList.toggle('cover', HIDE && focused);
}
document.querySelector('button').addEventListener('click', toggle);
</script>"""


def fixture(hide):
    rows = ''.join(f'<li>{escape(line)}</li>' for line in BOARD.splitlines())
    return FIXTURE.replace("ROWS", rows).replace("HIDE", str(hide).lower()).encode()


async def probe(config):
    browser = LiveBrowser(config)
    proofs = []
    async with Client(browser.transport, timeout=24) as relay, Client(create_server(browser), timeout=24) as driver:
        await browser.connect(relay)
        for label in ("A", "B"):
            for width, height in ((1440, 900), (390, 844)):
                view = f"{label}-{width}"
                await driver.call_tool("open_view", {"page_id": label, "width": width})

                async def key(value):
                    result = await driver.call_tool("act", {"action": "key", "value": value})
                    assert "journey" not in result.data
                    return result.data

                async def shot(suffix):
                    result = await driver.call_tool("capture", {"label": f"{view}-{suffix}"})
                    meta = json.loads(result.content[0].text)
                    path = browser.evidence / meta["path"]
                    png = path.read_bytes()
                    assert sha256(png) == meta["sha256"]
                    assert png == base64.b64decode(result.content[1].data)
                    assert struct.unpack(">II", png[16:24]) == (width, height)
                    return meta["sha256"]

                before = await shot("before")
                assert (await key("Tab"))["focus"]["label"] == "Inspect"
                assert (await key("Enter"))["focus"]["label"] == "Restore queue"
                focused = await shot("focused")
                assert (await key("Space"))["focus"]["label"] == "Inspect"
                after = await shot("after")
                if label == "A":
                    assert (await key("Enter"))["focus"]["label"] == "Restore queue"
                    assert (await key("Enter"))["focus"]["label"] == "Inspect"
                rows = [json.loads(line) for line in (browser.evidence / "audit.jsonl").read_text().splitlines()]
                start = max(index for index, row in enumerate(rows) if row["op"] == "open_view")
                audit = audit_journey(rows[start + 1:], 0, 3, 5, CONTRACT)
                assert audit["passed"] is (label == "A"), (view, audit)
                expected_failures = [] if label == "A" else ["deadline_visible"]
                assert [name for name, value in audit["checks"].items() if not value] == expected_failures, (view, audit)
                proofs.append({"view": view, "sha256": [before, focused, after], "outcomes": audit})
        await relay.call_tool("execute", {"session": browser.session, "code": "await state.view?.close();"})
        await relay.call_tool("session_delete", {"session": browser.session})
    return proofs


with ExitStack() as stack:
    profile = OUT / "chrome-profile"
    chrome = stack.enter_context(child([str(CHROME), "--headless", "--no-first-run", "--disable-extensions",
                                        "--disable-background-networking", "--remote-debugging-address=127.0.0.1",
                                        "--remote-debugging-port=0", f"--user-data-dir={profile}",
                                        "about:blank"], OUT / "chrome.log"))
    port = wait_ready(chrome, lambda: int((profile / "DevToolsActivePort").read_text().splitlines()[0]))
    browser = wait_ready(chrome, lambda: query_json(f"http://127.0.0.1:{port}/json/version"))
    relay_port = dynamic_port()
    relay = stack.enter_context(child([str(PLAYWRITER), "serve", "--host", "127.0.0.1"], OUT / "relay.log",
                                     env={**os.environ, "PLAYWRITER_PORT": str(relay_port),
                                          "PLAYWRITER_LOG_FILE_PATH": str(OUT / "playwriter.log")}))
    def relay_ready():
        with socket.create_connection(("127.0.0.1", relay_port), timeout=1):
            return True
    wait_ready(relay, relay_ready)
    pages = {}
    for label in ("A", "B"):
        server = stack.enter_context(fixture_server())
        server.fixture = fixture(label == "B")
        pages[label] = f"http://127.0.0.1:{server.server_port}/index.html"
    proofs = asyncio.run(probe({"cdp": browser["webSocketDebuggerUrl"], "pages": pages, "relay_port": relay_port,
                                "playwriter": str(PLAYWRITER), "evidence_dir": str(OUT / "captures"),
                                "observe_journey": True, "original_capture": True}))
    (OUT / "result.json").write_text(json.dumps({"browser": browser["Browser"], "scenarios": proofs}, indent=2) + "\n")
    print((OUT / "result.json").read_text())
