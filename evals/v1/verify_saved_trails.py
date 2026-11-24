"""Replay the two frozen saved-trails fixtures in real Chrome through Playwriter."""
import argparse
import asyncio
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import socket
import struct
import subprocess

from fastmcp import Client

from live_browser import LiveBrowser
from render import child, dynamic_port, fixture_server, query_json, wait_ready


async def focus_action(browser, view, name):
    for _ in range(12):
        focus = view["focus"]
        if focus["tag"] == "button" and re.match(rf"{name}\b", focus["label"], re.I):
            assert focus["visible"] and focus["document_focused"], focus
            return view
        view = await browser.act("key", "Tab")
    raise AssertionError(f"Could not reach {name} by keyboard")


async def verify(browser):
    journeys = []
    async with Client(browser.transport, timeout=24) as connection:
        await browser.connect(connection)
        for arm in browser.pages:
            for width, height in ((1440, 900), (390, 844)):
                view = await browser.open_view(arm, width)
                assert view["width"] == width and view["height"] == height
                assert re.search(r"\b0 (?:trails )?saved\b", view["ax"]), view["ax"]
                assert "Cedar Bend" in view["ax"] and "2.4 miles" in view["ax"], view["ax"]
                save = await focus_action(browser, view, "save")
                await browser.capture(f"{arm}-{width}-entry")
                result = await browser.act("key", "Enter")
                assert re.search(r"\b1 (?:trail )?saved\b", result["ax"]), result["ax"]
                assert "Cedar Bend" in result["ax"] and "2.4 miles" in result["ax"], result["ax"]
                remove = await focus_action(browser, result, "remove")
                await browser.capture(f"{arm}-{width}-saved")
                restored = await browser.act("key", "Enter")
                assert re.search(r"\b0 (?:trails )?saved\b", restored["ax"]), restored["ax"]
                assert "Cedar Bend" in restored["ax"] and "2.4 miles" in restored["ax"], restored["ax"]
                returned = await focus_action(browser, restored, "save")
                await browser.capture(f"{arm}-{width}-restored")
                assert all(state["url"] == view["url"] and state["layout_width"] <= width
                           for state in (view, save, result, remove, restored, returned))
                journeys.append({
                    "arm": arm, "viewport": [width, height], "route_miles": 2.4, "saved_counts": [0, 1, 0],
                    "keyboard_focus": [state["focus"]["label"] for state in (save, remove, returned)],
                    "focus_immediately_after_activation": [state["focus"] for state in (result, restored)],
                    "accessible_states": [state["ax"] for state in (view, result, restored)],
                })
        await connection.call_tool("session_delete", {"session": browser.session})
    return journeys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome", required=True, type=Path)
    parser.add_argument("--playwriter", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    specs = Path(__file__).parent
    fixture_dir = specs / "fixtures" / "saved-trails-shadcn"
    expected = json.loads((specs / "shadcn-saved-trails.json").read_bytes())
    args.out.mkdir(parents=True)
    portable_chrome = [
        str(args.chrome), "--headless", "--disable-extensions", "--disable-sync", "--no-first-run",
        "--no-default-browser-check", "--disable-background-networking", "--disable-component-update",
        f"--user-data-dir={args.out.resolve() / 'profile'}",
        "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=0", "about:blank",
    ]
    port = dynamic_port()
    env = {k: v for k, v in os.environ.items() if not k.startswith("PLAYWRITER_")}
    env.update(PLAYWRITER_PORT=str(port))
    files = {}
    with ExitStack() as stack:
        chrome = stack.enter_context(child(portable_chrome, args.out / "chrome.log"))
        port_marker = (args.out / "profile" / "DevToolsActivePort")
        cdp_port = wait_ready(chrome, lambda: int(port_marker.read_text().splitlines()[0]))
        identity = wait_ready(chrome, lambda: query_json(f"http://127.0.0.1:{cdp_port}/json/version"))
        assert identity["Browser"] == expected["spec"]["browser"], identity["Browser"]
        playwriter_version = subprocess.check_output([args.playwriter, "--version"], text=True).strip()
        assert playwriter_version == "0.12.0", playwriter_version
        relay = stack.enter_context(child([str(args.playwriter), "serve", "--host", "127.0.0.1"],
                                          args.out / "relay.log", env=env))

        def ready():
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True

        wait_ready(relay, ready)
        pages = {}
        for arm in expected["spec"]["arms"]:
            fixture = fixture_dir / arm
            receipt = json.loads((fixture / "receipt.json").read_bytes())
            raw = (fixture / "index.html").read_bytes()
            assert receipt["status"] == "passed" and receipt["html_sha256"] == sha256(raw).hexdigest()
            files[arm] = receipt["html_sha256"]
            server = stack.enter_context(fixture_server())
            server.fixture = raw
            pages[arm] = f"http://127.0.0.1:{server.server_port}/index.html"
        browser = LiveBrowser({"cdp": identity["webSocketDebuggerUrl"], "playwriter": str(args.playwriter),
                               "relay_port": port, "pages": pages,
                               "evidence_dir": str(args.out / "captures"), "original_capture": True})
        journeys = asyncio.run(verify(browser))

    screenshots = {}
    for journey in journeys:
        width, height = journey["viewport"]
        for state in ("entry", "saved", "restored"):
            path = args.out / "captures" / f"{journey['arm']}-{width}-{state}.png"
            raw = path.read_bytes()
            assert struct.unpack(">II", raw[16:24]) == (width, height)
            screenshots[path.name] = {"sha256": sha256(raw).hexdigest(), "dimensions": [width, height]}
    report = {"browser": identity["Browser"], "playwriter": playwriter_version, "fixture_hashes": files,
              "journeys": journeys, "screenshots": screenshots}
    (args.out / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print("SAVED_TRAILS_RECEIPT " + json.dumps(report, separators=(",", ":")))


if __name__ == "__main__":
    main()
