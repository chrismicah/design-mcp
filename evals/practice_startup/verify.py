"""Verify variant and screenshot identities and report the held-font outcome."""

from hashlib import sha256
import json
from pathlib import Path
import struct
import sys

def read(path):
    return json.loads(path.read_bytes())

root = Path(sys.argv[1])
summary = {}
for case in ("dayton-physiotherapy", "tacoma-eye-care"):
    versions = {}
    parents = set()
    for label in ("blocking", "deferred"):
        arm = root / case / label
        raw = (arm / "index.html").read_bytes()
        receipt = read(arm / "receipt.json")
        render = read(arm / "render.json")
        assert render["browser"] == "Chrome/157.0.8103.79" and render["renderer"] == "0.12.0"
        assert sha256(raw).hexdigest() == receipt["html_sha256"] == render["input_sha256"]
        assert receipt["case"] == case and receipt["label"] == label
        parents.add(receipt["parent_html_sha256"])
        capture = render["captures"]["390"]
        assert capture["status"] == "rendered", capture
        assert capture["pending"] and capture["fontRequests"] == 1 and not capture["errors"]
        png = (arm / "390.png").read_bytes()
        assert png.startswith(b"\x89PNG\r\n\x1a\n") and struct.unpack(">II", png[16:24]) == (390, 844)
        assert sha256(png).hexdigest() == capture["sha256"]
        assert capture["released"]["first_contentful_paint_ms"] is not None
        held = capture["held"]
        usable = (held["first_contentful_paint_ms"] is not None and held["call_focused"] and
                  held["call_in_view"] and held["heading_in_view"])
        versions[label] = {**capture, "usable_before_release": usable, "html_sha256": receipt["html_sha256"]}
    assert len(parents) == 1 and versions["blocking"]["html_sha256"] in parents
    for key in ("call_label", "heading"):
        assert versions["blocking"]["released"][key] == versions["deferred"]["released"][key]
    summary[case] = versions

(root / "startup-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
for case, versions in summary.items():
    print(case, {label: row["usable_before_release"] for label, row in versions.items()})
