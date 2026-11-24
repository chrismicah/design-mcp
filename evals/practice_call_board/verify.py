"""Check archive identity and derive eligibility from actual browser receipts."""

from hashlib import sha256
import json
from pathlib import Path
import struct
import sys


SIZES = {320: 700, 390: 844, 1440: 900}
REQUIRED = {
    "nameInitiallyVisible", "previewInitiallyVisible", "openingIdentity",
    "openingHours", "openingServices", "openingPhone", "openingWidth",
    "contactFocus", "serviceSelected", "emptyNameRecovery", "errorVisible",
    "selectionAfterError", "previewFocused", "previewReady", "previewInFirstViewport",
    "statusAnnouncement", "honestResultVisible", "reachEditableDraft", "editableDraft",
    "returnToOriginal", "noNetworkSubmission", "noPageErrors", "finalWidth",
}


def digest(data):
    return sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def verify_frames(cell, view, width, height):
    interaction = view["interaction"]
    required = {"before", "invalid"}
    if interaction["checks"]["previewReady"]:
        required.add("preview")
    assert set(interaction["frames"]) == required
    for phase, frame in interaction["frames"].items():
        suffix = "" if phase == "before" else f"-{phase}"
        assert frame["file"] == f"{width}{suffix}.png"
        image = (cell / frame["file"]).read_bytes()
        assert image.startswith(b"\x89PNG\r\n\x1a\n")
        assert struct.unpack(">II", image[16:24]) == (width, height)
        assert digest(image) == frame["sha256"]
        if phase == "before":
            assert frame["sha256"] == view["sha256"]


def verify(source, staged):
    rows = {}
    assert {p.parent.name for p in staged.glob("*/index.html")} == {p.parent.name for p in source.glob("*/index.html")}
    for src in sorted(source.glob("*/index.html")):
        arm = src.parent.name
        cell = staged / arm
        raw = (cell / "index.html").read_bytes()
        assert raw == src.read_bytes()
        render = read(cell / "render.json")
        meta = read(cell / "receipt.json")
        assert meta == read(src.with_name("receipt.json"))
        assert meta["arm"] == arm and meta["status"] == "passed"
        assert digest(raw) == render["input_sha256"] == meta["html_sha256"]
        assert render["browser"] == "Chrome/157.0.8103.79" and render["renderer"] == "0.12.0"
        assert set(render["captures"]) == {str(width) for width in SIZES}
        sizes = {}
        for width, height in SIZES.items():
            view = render["captures"][str(width)]
            assert view["status"] == "rendered", (arm, width, view)
            interaction = view["interaction"]
            assert interaction["viewport"] == {"width": width, "height": height}
            checks = interaction["checks"]
            assert REQUIRED <= checks.keys()
            assert all(type(passed) is bool for passed in checks.values())
            if source.name in {"madison-counseling", "albany-physiotherapy"}:
                frame = interaction["firstFrame"] or {}
                assert "editorFocusedInFirstFrame" in checks
                assert checks["disclosureVisibleInFirstFrame"] is (frame.get("localDisclosureVisible") is True)
                if checks["editorFocusedInFirstFrame"]:
                    assert frame["focusIsEditable"] is True and frame["focusTag"] == "TEXTAREA"
                if arm == "authored-compact-status" and checks["returnToOriginal"]:
                    assert interaction["statusAfterReturn"] == [""]
                if source.name == "albany-physiotherapy":
                    assert checks["statusClearedAfterReturn"] is (
                        checks["returnToOriginal"] and interaction["statusAfterReturn"] == [""]
                    )
                if arm == "call-slip-authored":
                    assert {"exampleVisibleAtOpening", "exampleReplacedByPreview", "exampleRestoredOnReturn"} <= checks.keys()
            verify_frames(cell, view, width, height)
            sizes[width] = {"failed": sorted(key for key, ok in checks.items() if not ok),
                            "request_count": len(interaction["requests"]),
                            "form": interaction["initialForm"], "first_frame": interaction["firstFrame"]}
        rows[arm] = {"html_sha256": meta["html_sha256"], "screens": sizes,
                     "eligible": all(not size["failed"] and not size["request_count"] for size in sizes.values())}
    if source.name == "tacoma-eye-care":
        assert rows["call-board"]["eligible"], "The authored healthy control no longer passes."
    return rows


if __name__ == "__main__":
    root = Path(__file__).resolve().parent / "cells"
    cells = Path(sys.argv[1])
    for case in sorted(p for p in root.iterdir() if p.is_dir()):
        result = verify(case, cells / case.name)
        suffix = "" if case.name == "tacoma-eye-care" else f"-{case.name}"
        (cells / f"verified-summary{suffix}.json").write_text(json.dumps(result, indent=2) + "\n")
        print(case.name, "Verified trace identities and capture hashes:",
              {arm: row["eligible"] for arm, row in result.items()})
