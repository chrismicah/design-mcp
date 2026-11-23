"""Verify the exact four archived practice drafts before rendering."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
cells = ROOT / "cells/tacoma-eye-care"
previous = "589215a5c7efb1c4c47bc581814a29ad829252d8b5f0b5d45430d15812229e66"
for arm in ("focus-repair", "call-board", "earlier-draft", "visible-handoff"):
    cell = cells / arm
    row = json.loads((cell / "receipt.json").read_bytes())
    digest = sha256((cell / "index.html").read_bytes()).hexdigest()
    assert row["arm"] == arm and row["html_sha256"] == digest and row["status"] == "passed"
    if arm == "focus-repair":
        assert digest == previous
    print(arm, digest)
shutil.copytree(ROOT / "cells", sys.argv[1])
