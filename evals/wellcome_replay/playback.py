"""Measure the unchanged ordinary-client result at three live widths."""
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT.parent / "v1"))
import render

render.VIEWPORTS = ((320, 700), (390, 844), (1440, 900))
HEIGHTS = dict(render.VIEWPORTS)
ASSET = json.loads((ROOT / "asset.json").read_text())


async def check(client, cell, width):
    generation = json.loads((cell / "generation.json").read_text())
    assert sha256((cell / "index.html").read_bytes()).hexdigest() == generation["html_sha256"]
    paths = {label: cell / f"{width}-{label}.png" for label in ("open", "closed", "touch")}
    body = "\n".join([
        f"const spec = {json.dumps(ASSET)};",
        "const paths = " + json.dumps({key: str(path) for key,path in paths.items()}) + ";",
        (ROOT / "measure-image-focus.js").read_text(),
        (ROOT / "map-annotation-geometry.js").read_text(),
        (ROOT / "replay.js").read_text(),
    ])
    response = await render.execute(client, body)
    line = next((line for line in response.splitlines() if "ORDINARY " in line),None)
    if line is None:
        raise RuntimeError(response[-1800:])
    row, _ = json.JSONDecoder().raw_decode(line.split("ORDINARY ",1)[1])
    row["frames"] = {}
    for label,path in {"before":cell/f"{width}.png",**paths}.items():
        if not path.is_file():
            continue
        raw = path.read_bytes()
        assert raw.startswith(b"\x89PNG\r\n\x1a\n")
        assert struct.unpack(">II",raw[16:24]) == (width,HEIGHTS[width])
        row["frames"][label] = {"file":path.name,"sha256":sha256(raw).hexdigest()}
    print(cell.name,width,[key for key,value in row["checks"].items() if not value],flush=True)
    return row


if __name__=="__main__":
    render.main(check)
