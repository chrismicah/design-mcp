"""Verify the exact archived practice drafts before rendering."""

from difflib import unified_diff
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
dayton = ROOT / "cells/dayton-physiotherapy/unified-composition"
if dayton.is_dir():
    proof = ROOT.parents[1] / "evidence/benchmark-v1/dayton-initial-installed.json"
    dayton_install = json.loads(proof.read_bytes())
    row = json.loads((dayton / "receipt.json").read_bytes())
    assert row["case"] == dayton.parent.name and row["arm"] == dayton.name and row["status"] == "passed"
    assert row["commit"] == dayton_install["candidate"]
    assert row["reply_sha256"] == dayton_install["reply_sha256"]
    assert sha256((dayton / "index.html").read_bytes()).hexdigest() == row["html_sha256"]
    assert row["html_sha256"] == dayton_install["html_sha256"]
    assert len(dayton_install["install_receipts"]) == 4
    print(row["case"], row["arm"], row["html_sha256"])

    repair = dayton.with_name("focus-editable-note")
    if repair.is_dir():
        parent = (dayton / "index.html").read_bytes()
        fixed = (repair / "index.html").read_bytes()
        repair_receipt = json.loads((repair / "receipt.json").read_bytes())
        old = b"draft.focus({ preventScroll: true });"
        new = b"draftText.focus({ preventScroll: true });"
        assert repair_receipt["case"] == dayton.parent.name and repair_receipt["arm"] == repair.name
        assert repair_receipt["parent_html_sha256"] == row["html_sha256"]
        assert sha256(fixed).hexdigest() == repair_receipt["html_sha256"]
        assert parent.count(old) == 1 and new not in parent and fixed == parent.replace(old, new)
        print(repair_receipt["case"], repair_receipt["arm"], repair_receipt["html_sha256"])

def verify_installed_pair(case, prefix, proof_name):
    proof = ROOT.parents[1] / "evidence" / "benchmark-v1" / proof_name
    installed_focus = json.loads(proof.read_bytes())
    assert installed_focus["kind"] == "installed" and len(installed_focus["installs"]) == 4
    expected = installed_focus["practices"][case.name]
    pair = {}
    for arm in ("control", "treatment"):
        draft = case / f"{prefix}-{arm}"
        stamp = json.loads((draft / "receipt.json").read_bytes())
        assert stamp["status"] == "passed" and stamp["case"] == case.name and stamp["arm"] == draft.name
        assert stamp["commit"] == installed_focus["commits"][arm]
        assert stamp["reply_sha256"] == expected["reply_sha256"][arm]
        assert stamp["html_sha256"] == sha256((draft / "index.html").read_bytes()).hexdigest()
        pair[arm] = stamp
        print(stamp["case"], stamp["arm"], stamp["html_sha256"])
    for key in ("model", "effort", "shell_tool", "prompt_prefix_sha256"):
        assert pair["control"][key] == pair["treatment"][key], key
    assert pair["control"]["thread_id"] != pair["treatment"]["thread_id"]
    return pair


madison = ROOT / "cells/madison-counseling"
if madison.is_dir():
    pair = verify_installed_pair(madison, "focus", "focus-guidance-installed.json")
    compact = madison / "authored-compact-status"
    if compact.is_dir():
        original = (madison / "focus-treatment/index.html").read_text()
        revised = (compact / "index.html").read_text()
        stamp = json.loads((compact / "receipt.json").read_bytes())
        diff = "".join(unified_diff(original.splitlines(keepends=True), revised.splitlines(keepends=True)))
        assert stamp["case"] == madison.name and stamp["arm"] == compact.name
        assert stamp["parent_html_sha256"] == pair["treatment"]["html_sha256"]
        assert stamp["html_sha256"] == sha256(revised.encode()).hexdigest()
        assert stamp["unified_diff_sha256"] == sha256(diff.encode()).hexdigest()
        print(stamp["case"], stamp["arm"], stamp["html_sha256"])

albany = ROOT / "cells/albany-physiotherapy"
if albany.is_dir():
    pair = verify_installed_pair(albany, "compact-status", "compact-status-guidance-installed.json")
    slip = albany / "call-slip-authored"
    if slip.is_dir():
        stamp = json.loads((slip / "receipt.json").read_bytes())
        assert stamp["case"] == albany.name and stamp["arm"] == slip.name
        assert stamp["scope"] == "Authored composition"
        assert stamp["control_html_sha256"] == pair["control"]["html_sha256"]
        assert stamp["html_sha256"] == sha256((slip / "index.html").read_bytes()).hexdigest()
        print(stamp["case"], stamp["arm"], stamp["html_sha256"])
        parent = stamp
        for arm, scope in (
            ("call-slip-live-example", "Authored selected-visit repair"),
            ("call-slip-form-balance", "Authored form balance repair"),
        ):
            cell = albany / arm
            if not cell.is_dir():
                break
            repaired = json.loads((cell / "receipt.json").read_bytes())
            assert repaired["case"] == albany.name and repaired["arm"] == cell.name
            assert repaired["scope"] == scope
            assert repaired["parent_html_sha256"] == parent["html_sha256"]
            assert repaired["html_sha256"] == sha256((cell / "index.html").read_bytes()).hexdigest()
            print(repaired["case"], repaired["arm"], repaired["html_sha256"])
            parent = repaired

        integrated = albany / "call-slip-integrated"
        if integrated.is_dir():
            stamp = json.loads((integrated / "receipt.json").read_bytes())
            selected = json.loads((albany / "call-slip-live-example/receipt.json").read_bytes())
            assert stamp["case"] == albany.name and stamp["arm"] == integrated.name
            assert stamp["scope"] == "Authored integrated call slip"
            assert stamp["parent_html_sha256"] == selected["html_sha256"]
            assert stamp["html_sha256"] == sha256((integrated / "index.html").read_bytes()).hexdigest()
            print(stamp["case"], stamp["arm"], stamp["html_sha256"])

shutil.copytree(ROOT / "cells", sys.argv[1])
