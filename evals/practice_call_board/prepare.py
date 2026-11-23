"""Verify the exact archived practice drafts before rendering."""

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
cells = ROOT / "cells/tacoma-eye-care"
previous = "589215a5c7efb1c4c47bc581814a29ad829252d8b5f0b5d45430d15812229e66"
arms = (
    "focus-repair", "call-board", "earlier-draft", "visible-handoff", "unified-composition",
    "single-service", "single-service-trimmed", "reaction-control", "reaction-repair",
)
receipts = {}
for arm in arms:
    cell = cells / arm
    row = json.loads((cell / "receipt.json").read_bytes())
    digest = sha256((cell / "index.html").read_bytes()).hexdigest()
    assert row["arm"] == arm and row["html_sha256"] == digest and row["status"] == "passed"
    if arm == "focus-repair":
        assert digest == previous
    receipts[arm] = row
    print(arm, digest)

installed = json.loads((ROOT.parents[1] / "evidence/benchmark-v1/opening-view-reaction-installed.json").read_bytes())
control = receipts["reaction-control"]
repair = receipts["reaction-repair"]
parent = receipts["unified-composition"]
assert installed["complete_architecture_pair"]
assert control["received_render_feedback"] is False and repair["received_render_feedback"] is True
assert control["commit"] == parent["commit"] and repair["commit"] == installed["candidate"]
assert control["parent_html_sha256"] == repair["parent_html_sha256"] == parent["html_sha256"]
assert parent["html_sha256"] == installed["captured_html_sha256"]
assert repair["replay_summary_sha256"] == installed["capture_summary_sha256"]
assert control["thread_id"] != repair["thread_id"]
assert control["prompt_sha256"] != repair["prompt_sha256"]
for key in ("case", "model", "effort", "shell_tool", "prompt_prefix_sha256", "replay_summary_sha256"):
    assert control[key] == repair[key], key
reply = json.dumps(installed["measured_reaction"], ensure_ascii=False, sort_keys=True)
assert control["reply_sha256"] == sha256(b"null").hexdigest()
assert repair["reply_sha256"] == sha256(reply.encode()).hexdigest()
shutil.copytree(ROOT / "cells", sys.argv[1])
