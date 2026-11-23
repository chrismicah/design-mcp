"""Replay the frozen consultation drafts through the existing Playwriter harness."""

from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [os.environ["PRACTICE_RENDER_HARNESS"], str(HERE.parent / "v1")]
import render


render.VIEWPORTS = ((320, 700), (390, 844), (1440, 900))
HEIGHTS = dict(render.VIEWPORTS)
PRACTICES = json.loads((HERE / "practice-fixtures.json").read_bytes())


async def interact(client, cell, width):
    paths = {name: cell / f"{width}-{name}.png" for name in ("invalid", "preview")}
    code = "const practice = " + json.dumps(PRACTICES[cell.parent.name]) + ";\n"
    code += "const paths = " + json.dumps({key: str(value) for key, value in paths.items()}) + ";\n"
    answer = await render.execute(client, code + (HERE / "call-board-replay.js").read_text())
    line = next((line for line in answer.splitlines() if "PRACTICE_REPLAY " in line), None)
    if line is None:
        raise RuntimeError("No interaction receipt: " + answer[-1500:])
    row, _ = json.JSONDecoder().raw_decode(line.split("PRACTICE_REPLAY ", 1)[1])
    row["frames"] = {}
    for key, path in {"before": cell / f"{width}.png", **paths}.items():
        if path.is_file():
            raw = path.read_bytes()
            assert raw.startswith(b"\x89PNG\r\n\x1a\n") and struct.unpack(">II", raw[16:24]) == (width, HEIGHTS[width])
            row["frames"][key] = {"sha256": sha256(raw).hexdigest(), "file": path.name}
    print(cell.name, width, [key for key, value in row["checks"].items() if not value], flush=True)
    return row


if __name__ == "__main__":
    render.main(interact)
