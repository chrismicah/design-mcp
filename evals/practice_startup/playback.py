"""Replay first paint with a held font stylesheet, using the pinned Chrome harness."""

from hashlib import sha256
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path[:0] = [os.environ["PRACTICE_RENDER_HARNESS"], str(ROOT.parent / "v1")]
import render

render.VIEWPORTS = ((390, 844),)


async def capture(client, cell, width, height, url, _interact, **_options):
    shot = cell / f"{width}.png"
    args = json.dumps({"width": width, "height": height, "url": url, "shot": str(shot),
                       "fontMode": os.environ.get("PRACTICE_FONT_MODE", "synthetic")})
    response = await render.execute(client, f"const spec = {args};\n" + (ROOT / "startup.js").read_text())
    line = next((line for line in response.splitlines() if "STARTUP_RESULT " in line), None)
    if line is None or not shot.is_file():
        raise RuntimeError("Missing startup receipt: " + response[-1200:])
    row, _ = json.JSONDecoder().raw_decode(line.split("STARTUP_RESULT ", 1)[1])
    return {"status": "rendered", "sha256": sha256(shot.read_bytes()).hexdigest(), **row}


render.capture = capture
render.main()
