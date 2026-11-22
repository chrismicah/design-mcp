"""Drive the one disposable Chrome started by the local URL reviewer."""

import asyncio
from datetime import datetime, timezone
import json
from time import perf_counter
from urllib.parse import urlsplit

from .address import credentials_reason, local_address_reason
from .evidence import SCHEMA, EvidenceError, inspect_url
from .isolated import COLLECTOR, VIEWPORTS, CaptureError, collect_expression
from .pipeline import _ms


class ChromeSession:
    def __init__(self, socket):
        self.socket = socket
        self.sequence = 0
        self.loaded = set()

    async def receive(self):
        reply = json.loads(await self.socket.recv())
        if reply.get("method") == "Page.lifecycleEvent" and reply["params"]["name"] == "DOMContentLoaded":
            event = reply["params"]
            self.loaded.add((reply["sessionId"], event["frameId"], event["loaderId"]))
        return reply

    async def call(self, method, session=None, **params):
        self.sequence += 1
        message = {"id": self.sequence, "method": method, "params": params}
        if session is not None:
            message["sessionId"] = session
        await self.socket.send(json.dumps(message))
        while True:
            reply = await self.receive()
            if reply.get("id") == self.sequence:
                if "error" in reply:
                    raise RuntimeError(f"Chrome could not complete {method}")
                return reply["result"]

    async def new_page(self):
        target = await self.call("Target.createTarget", url="about:blank")
        attached = await self.call("Target.attachToTarget", targetId=target["targetId"], flatten=True)
        return attached["sessionId"]

    async def evaluate(self, session, expression, **options):
        reply = await self.call("Runtime.evaluate", session, expression=expression, returnByValue=True,
                                awaitPromise=True, **options)
        if "exceptionDetails" in reply:
            raise RuntimeError("Chrome could not read the captured view")
        return reply["result"]["value"]


async def capture_page(url, web_socket, viewport=VIEWPORTS[0]):
    from websockets.asyncio.client import connect

    # Only the loopback Chrome subprocess we just started can supply a socket here.
    endpoint = urlsplit(web_socket)
    if endpoint.scheme != "ws" or endpoint.hostname != "127.0.0.1":
        raise ValueError("Expected the isolated browser's local address")

    async with connect(web_socket, proxy=None, open_timeout=4, close_timeout=1, max_size=20 * 1024 * 1024) as socket:
        browser = ChromeSession(socket)
        page = await browser.new_page()
        width, height = viewport
        await browser.call("Emulation.setDeviceMetricsOverride", page, width=width, height=height,
                           deviceScaleFactor=1, mobile=False)
        await browser.call("Emulation.setEmulatedMedia", page, features=[{"name": "prefers-reduced-motion", "value": "reduce"}])
        await browser.call("Page.enable", page)
        await browser.call("Page.setLifecycleEventsEnabled", page, enabled=True)
        started = perf_counter()
        navigation = await browser.call("Page.navigate", page, url=url)
        if navigation.get("errorText") or not navigation.get("loaderId") or navigation.get("isDownload"):
            raise CaptureError("Chrome couldn't open this page. Check the address and try again.")
        key = (page, navigation["frameId"], navigation["loaderId"])

        async def ready():
            while key not in browser.loaded:
                await browser.receive()

        try:
            await asyncio.wait_for(ready(), 18)
        except asyncio.TimeoutError:
            raise CaptureError("This page took too long to load. Try again or review it from its open tab.") from None
        loaded = perf_counter()

        async def current_document():
            current = (await browser.call("Page.getFrameTree", page))["frameTree"]["frame"]
            if (current["id"], current["loaderId"]) != key[1:]:
                raise CaptureError("The page changed during review. Try reviewing its final address.")
            return current["url"]

        final_url = await current_document()
        clean_url, removed = inspect_url(final_url)
        if removed:
            raise EvidenceError("credentials-in-url", credentials_reason(removed))
        if reason := local_address_reason(clean_url):
            raise EvidenceError("private-address", reason)
        world = await browser.call("Page.createIsolatedWorld", page, frameId=key[1])
        context = {"contextId": world["executionContextId"]}
        status = await browser.evaluate(page, "performance.getEntriesByType('navigation')[0]?.responseStatus || 0", **context)
        if status >= 400:
            raise CaptureError(f"The site returned HTTP {status}. Check that the page is public and try again.")
        await browser.evaluate(page, "Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 1000))]).then(() => true)", **context)
        frame = await browser.evaluate(page, collect_expression(), **context)
        picture = await browser.call("Page.captureScreenshot", page, format="png", fromSurface=True)
        # A changed document, viewport, or field layout invalidates the mask for these pixels.
        after = await browser.evaluate(page, collect_expression(), **context)
        if (await current_document() != final_url or any(after[field] != frame[field]
                for field in ("masks", "viewport", "document"))):
            raise CaptureError("The page moved during capture. Try again once it finishes loading.")
        # Paint over captured pixels in a blank document that the reviewed site cannot style.
        masker = await browser.new_page()
        mask_script = COLLECTOR.with_name("mask.js").read_text(encoding="utf-8")
        arguments = json.dumps([f"data:image/png;base64,{picture['data']}", frame["masks"]["boxes"]])
        masked = await browser.evaluate(masker, f"""(async () => {{ {mask_script}
            const data = await maskPagePicture(...{arguments});
            return {{data, thumbnail: await reviewThumbnail('data:image/png;base64,' + data)}};
        }})()""")
        frame["screenshot"] = {"media_type": "image/png", "data": masked["data"]}
        frame["masks"]["applied"] = True
        return {
            "schema": SCHEMA,
            "capture": {"source": "pasted-url", "url": clean_url, "title": frame.get("title"),
                        "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "user_triggered": True},
            "frames": [frame],
            "thumbnail": masked["thumbnail"],
            "timings_ms": {"page_load": _ms(started, loaded), "capture": _ms(loaded, perf_counter())},
            "url_capture_ms": {},
        }
