"""Report repeat-preview behavior and failures without assuming either arm wins."""
from hashlib import sha256
import json
from pathlib import Path
import struct
import sys

case = sys.argv[1]
folder = Path(sys.argv[2]) / case
results = {}
for arm in ("control", "treatment"):
    cell = folder / f"note-retention-{arm}"
    stamp = json.loads((cell / "receipt.json").read_bytes())
    render = json.loads((cell / "render.json").read_bytes())
    assert render["input_sha256"] == stamp["html_sha256"] == sha256((cell / "index.html").read_bytes()).hexdigest()
    results[arm] = {}
    for width, height in ((320, 700), (390, 844), (1440, 900)):
        screen = render["captures"][str(width)]
        if screen["status"] != "rendered":
            results[arm][width] = {"status": screen["status"], "message": screen["message"]}
            continue
        interaction = screen["interaction"]
        assert interaction["viewport"] == {"width": width, "height": height}
        for image in interaction["frames"].values():
            data = (cell / image["file"]).read_bytes()
            assert data.startswith(b"\x89PNG\r\n\x1a\n") and struct.unpack(">II", data[16:24]) == (width, height)
            assert sha256(data).hexdigest() == image["sha256"]
        failed = sorted(key for key, result in interaction["checks"].items() if not result)
        results[arm][width] = {
            "status": "passed" if not failed and not interaction["requests"] else "failed",
            "failed": failed,
            "draft_continuity": interaction.get("draftContinuity"),
            "post_load_requests": interaction["requests"],
            "captures": interaction["frames"],
        }
print(json.dumps({"case": case, "results": results}, indent=2))
