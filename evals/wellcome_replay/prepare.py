"""Recreate the three frozen HTML inputs from verified museum images."""
from base64 import b64encode
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
manifest = json.loads((ROOT / "manifest.json").read_bytes())
assets = {}
for marker, item in manifest["images"].items():
    with urlopen(item["url"], timeout=15) as response:
        blob = response.read(1_000_001)
    assert len(blob) <= 1_000_000 and sha256(blob).hexdigest() == item["sha256"], marker
    assets[marker.encode()] = b"data:image/jpeg;base64," + b64encode(blob)

for name, receipt in manifest["arms"].items():
    raw = (ROOT / f"{name}.html").read_bytes()
    assert sha256(raw).hexdigest() == receipt["raw_sha256"], name
    for marker, data in assets.items():
        assert marker in raw, (name, marker)
        raw = raw.replace(marker, data)
    assert sha256(raw).hexdigest() == receipt["html_sha256"], name
    cell = Path(sys.argv[1]) / "wellcome" / name
    cell.mkdir(parents=True)
    (cell / "index.html").write_bytes(raw)
    (cell / "generation.json").write_text(json.dumps(receipt))
