"""Check exact draft identity and stage a fresh browser input directory."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
case = root / "cells/tacoma-eye-care"
rows = {}
for arm in ("release", "omissions-trial"):
    cell = case / arm
    row = json.loads((cell / "receipt.json").read_bytes())
    assert row["status"] == "passed" and row["arm"] == arm
    assert row["html_sha256"] == sha256((cell / "index.html").read_bytes()).hexdigest()
    rows[arm] = row
for field in ("case", "model", "effort", "prompt_prefix_sha256", "shell_tool"):
    assert rows["release"][field] == rows["omissions-trial"][field]
assert len({row["thread_id"] for row in rows.values()}) == 2
assert len({row["reply_sha256"] for row in rows.values()}) == 2
shutil.copytree(root / "cells", sys.argv[1])
