"""From one capture to one critique and one preview file, all on this computer."""

import json
import os
import re
import sys
import time
from pathlib import Path

from .checks import local_findings
from .evidence import SCHEMA, UNKNOWN, EvidenceError, normalize
from .preview import after_matrix, build_preview

KEEP_REVIEWS = 20
NO_FINDING = (
    "No issues flagged in this view. Checked sideways scroll, covered buttons and text contrast on flat backgrounds."
)
FRONTIER = {
    "status": "not-run",
    "reason": "No visual review provider is set up in this build. Nothing was uploaded.",
}
_REVIEW_FOLDER = re.compile(r"c-[0-9a-f]{12}\Z")
_OWN_FILES = ("preview.html", "evidence.json")
_MASK_KINDS = ("field", "editable", "frame")


def state_dir(home=None, platform=None):
    """This tool's private folder inside the user's own directory."""
    home = Path(home) if home is not None else Path.home()
    if (platform or sys.platform) == "darwin":
        return home / "Library" / "Application Support" / "design-mcp"
    return home / ".local" / "state" / "design-mcp"


def _write_private(path, text):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(text)
    os.chmod(path, 0o600)


def _without_pixels(evidence):
    frames = [
        {**frame, "screenshot": {key: value for key, value in frame["screenshot"].items() if key != "data"}}
        for frame in evidence["frames"]
    ]
    return {**evidence, "frames": frames}


def _prune(root, keep, protect):
    """Drop the oldest reviews. Only folders this module names are touched, and only the files it writes."""
    folders = [path for path in root.iterdir()
               if _REVIEW_FOLDER.match(path.name) and path.is_dir() and not path.is_symlink()]
    folders.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for stale in folders[keep:]:
        if stale.name == protect:
            continue
        for name in _OWN_FILES:
            (stale / name).unlink(missing_ok=True)
        try:
            stale.rmdir()
        except OSError:
            pass


def _ms(start, end):
    return round((end - start) * 1000, 1)


def review(bundle, root=None, *, keep_latest=False):
    """Run the local review of one capture.

    Always returns a JSON-safe dict. `ok` False carries a stable `code` and a `message` for the person
    scanning. With no `root`, results go to this tool's private folder and only the newest are kept.
    Managed profile directories use the same limit with `keep_latest`.
    """
    started = time.perf_counter()
    try:
        evidence = normalize(bundle)
    except EvidenceError as error:
        return {"ok": False, "code": error.code, "message": error.message}
    cleaned = time.perf_counter()
    findings = local_findings(evidence)
    checked = time.perf_counter()
    document = build_preview(evidence, findings)

    if root is None:
        root = state_dir() / "reviews"
        keep_latest = True
    root = Path(root)
    folder = root / evidence["capture"]["id"]
    preview_path = folder / "preview.html"
    try:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        folder.mkdir(exist_ok=True, mode=0o700)
        _write_private(preview_path, document)
        _write_private(folder / "evidence.json",
                       json.dumps(_without_pixels(evidence), indent=2, ensure_ascii=False) + "\n")
        os.utime(folder)
        if keep_latest:
            _prune(root, KEEP_REVIEWS, folder.name)
    except OSError as error:
        return {
            "ok": False,
            "code": "cannot-save",
            "message": f"The preview could not be saved ({error.strerror or error}). Nothing else was changed.",
        }
    done = time.perf_counter()

    critique = findings[0] if findings else None
    frames = evidence["frames"]
    return {
        "ok": True,
        "schema": SCHEMA,
        "capture_id": evidence["capture"]["id"],
        "url": evidence["capture"]["url"],
        "critique": critique,
        "message": None if critique else NO_FINDING,
        "findings": findings,
        "more_findings": max(0, len(findings) - 1),
        "has_after": after_matrix(critique) is not None,
        "regions": sum(len(frame["regions"]) for frame in frames),
        "masked": {kind: sum(frame["masks"]["counts"][kind] for frame in frames) for kind in _MASK_KINDS},
        "preview_path": str(preview_path),
        "preview_url": preview_path.resolve().as_uri(),
        "timings_ms": {
            "page_load": evidence["timings_ms"]["page_load"],
            "capture": evidence["timings_ms"]["capture"],
            "sanitize": _ms(started, cleaned),
            "local_checks": _ms(cleaned, checked),
            "preview": _ms(checked, done),
            "frontier": FRONTIER["status"],
        },
        "frontier": dict(FRONTIER),
        "notes": evidence["notes"],
    }


def _duration(value):
    return UNKNOWN if value == UNKNOWN else f"{value} ms"


def describe(result):
    """Plain lines for a terminal: the finding, the change, the check, then where the preview is."""
    if not result["ok"]:
        return [result["message"]]
    critique, lines = result["critique"], []
    if critique:
        lines += [critique["problem"], f"Change: {critique['change']}", f"Check: {critique['outcome']}"]
        more = result["more_findings"]
        if more:
            lines.append(f"Also found: {more} more local finding{'' if more == 1 else 's'} (--json lists them).")
    else:
        lines.append(result["message"])
    kind = "before and after" if result["has_after"] else "captured view"
    lines.append(f"Preview ({kind}): {result['preview_path']}")
    lines.append("Visual review by a model: not run. Nothing was uploaded.")
    timings = result["timings_ms"]
    lines.append(
        f"Timing: page load {_duration(timings['page_load'])}, capture {_duration(timings['capture'])}, "
        f"local checks {_duration(timings['local_checks'])}, preview {_duration(timings['preview'])}."
    )
    return lines
