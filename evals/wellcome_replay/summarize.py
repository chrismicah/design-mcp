"""Retain observable metrics in CI logs without storing screenshots remotely."""
import json
from pathlib import Path
import sys

receipts = list(Path(sys.argv[1]).glob("wellcome/*/render.json"))
assert len(receipts) == 3
errors = []
for filename in sorted(receipts):
    data = json.loads(filename.read_bytes())
    name = filename.parent.name
    assert data["browser"] == "Chrome/157.0.8103.79", data["browser"]
    assert data["renderer"] == "0.12.0", data["renderer"]
    assert set(data["captures"]) == {"320", "390", "1440"}
    for width, capture in data["captures"].items():
        if capture["status"] != "rendered":
            errors.append((name, width, capture))
            continue
        interaction = capture["interaction"]
        assert "before" in interaction["frames"], (name, width)
        print("WELLCOME " + json.dumps({
            "arm": name, "width": width, "browser": data["browser"],
            "html_sha256": data["input_sha256"], "fonts": capture["loadedFonts"],
            "accessibility": capture["accessibility"],
            "checks": interaction["checks"], "frames": interaction["frames"],
            "opening": interaction.get("opening"), "open": interaction.get("open"),
            "projection": interaction.get("projection"),
            "annotations": interaction.get("annotations"),
            "touch_annotations": interaction.get("touchAnnotations"),
        }, separators=(",", ":")))
assert not errors, errors
