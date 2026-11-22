"""Bind a reaction-pilot ballot to independent live inputs and original PNGs."""

import argparse
import base64
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import struct

HEIGHTS = {1440: 900, 390: 844}
WEIGHTS = {"coherence": "0.30", "originality": "0.30", "craft": "0.20", "usability": "0.20"}
ACTIVATION = {"Enter", "Space"}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def screenshot(run, page, width, suffix, captures, calls):
    label = f"{page}-{width}-{suffix}"
    index, row = captures[label]
    assert row["page_id"] == page and row["path"] == f"{label}.png", label
    assert row["observation"]["width"] == width, label
    raw = (run / "captures" / row["path"]).read_bytes()
    assert raw.startswith(b"\x89PNG\r\n\x1a\n"), label
    assert struct.unpack(">II", raw[16:24]) == (width, HEIGHTS[width]), label
    assert sha256(raw) == row["sha256"], label
    matching = [call for call in calls if call["tool"] == "capture" and call["arguments"]["label"] == label]
    assert len(matching) == 1, label
    tool_call = matching[0]
    images = [block for block in tool_call["result"]["content"] if block["type"] == "image"]
    assert len(images) == 1 and images[0]["mimeType"] == "image/png", label
    assert base64.b64decode(images[0]["data"], validate=True) == raw, label
    return index, {"sha256": row["sha256"], "file": row["path"], "tool_call_id": tool_call["id"]}


def edge_actions(rows, after):
    actions = []
    for row in rows[after + 1:]:
        if row["op"] == "open_view":
            break
        if row["op"] == "act" and row.get("observation"):
            actions.append(row)
    return actions


def indexed_captures(rows):
    captured = {}
    for index, row in enumerate(rows):
        if row["op"] != "capture" or row.get("status") == "error":
            continue
        label = row["label"]
        assert label not in captured, label
        captured[label] = (index, row)
    return captured


def audit(run, cells, case):
    trace = (run / "critic.jsonl").read_bytes()
    log = (run / "captures/audit.jsonl").read_bytes()
    events, rows = read_jsonl(trace), read_jsonl(log)
    key = json.loads((run / "sealed-key.json").read_bytes())
    settings = json.loads((run / "driver-config.json").read_bytes())
    assert settings["original_capture"] is True and set(settings["pages"]) == set(key) == {"A", "B"}
    assert {value["arm"] for value in key.values()} == {"plain", "design-mcp"}
    builder_threads = set()
    for entry in key.values():
        cell = cells / case / entry["arm"]
        receipt = json.loads((cell / "receipt.json").read_bytes())
        assert receipt["html_sha256"] == entry["html_sha256"] == sha256((cell / "index.html").read_bytes())
        assert receipt["thread_id"] == entry["thread_id"]
        builder_threads.add(entry["thread_id"])
    threads = [event["thread_id"] for event in events if event["type"] == "thread.started"]
    completed = [event for event in events if event["type"] == "turn.completed"]
    assert len(builder_threads) == 2 and len(threads) == len(completed) == 1
    assert threads[0] not in builder_threads and completed[0].get("usage")
    items = [event["item"] for event in events if event["type"] == "item.completed"]
    assert all(item["type"] in {"agent_message", "reasoning", "mcp_tool_call"} for item in items)
    calls = [item for item in items if item["type"] == "mcp_tool_call"]
    allowed = {"open_view", "act", "capture"}
    assert all(item["server"] == "review" and item["tool"] in allowed for item in calls)
    calls = [item for item in calls if item["status"] == "completed"]
    reply = [item["text"] for item in items if item["type"] == "agent_message"][-1]
    fenced = re.fullmatch(r"\s*```json\s*(.*?)\s*```\s*", reply, re.DOTALL)
    ballot = json.loads(fenced[1] if fenced else reply)
    screens = ballot["screens"]
    assert set(screens) <= {f"{page}-{width}" for page in key for width in HEIGHTS}
    captures = indexed_captures(rows)
    for label, verdict in screens.items():
        page, width_text = label.split("-")
        width = int(width_text)
        endpoint = settings["pages"][page]
        before, first = screenshot(run, page, width, "before", captures, calls)
        after, last = screenshot(run, page, width, "after", captures, calls)
        assert before < after, label
        opened = next(row for row in reversed(rows[:before]) if row["op"] == "open_view")
        assert opened["page_id"] == page and opened["width"] == width, label
        phase = rows[before:after + 1]
        assert all(row["op"] != "open_view" and row["page_id"] == page for row in phase), label
        observed = [row for row in phase if row.get("observation")]
        assert all(row["observation"]["url"] == endpoint for row in observed), label
        actions = [row for row in observed if row["op"] == "act"]
        assert any(row["action"] == "key" and row["value"] in ACTIVATION for row in actions), label
        edge = edge_actions(rows, after)
        assert edge and all(row["page_id"] == page and row["observation"]["url"] == endpoint for row in edge), label
        for metric in WEIGHTS:
            assert type(verdict[metric]) in (int, float) and 0 <= verdict[metric] <= 10, label
        for field in ("input", "expected", "observed"):
            assert verdict["primary_action"][field].strip(), label
        for field in ("edge_observation", "strength", "weakness", "repair"):
            assert verdict[field], label
        score = sum(Decimal(str(verdict[k])) * Decimal(w) for k, w in WEIGHTS.items())
        verdict.update(
            arm=key[page]["arm"], html_sha256=key[page]["html_sha256"], weighted=float(score),
            before=first, after=last, layout_width=rows[after]["observation"]["layout_width"],
            input_sequence=[{"action": row["action"], "value": row["value"]} for row in actions],
            edge_inputs=[{"action": row["action"], "value": row["value"]} for row in edge],
        )
    return {
        **ballot, "case": case, "verified_screens": len(screens), "required_screens": 4,
        "browser": (run / "browser-version.txt").read_text().strip(),
        "evaluator_thread": threads[0], "usage": completed[0]["usage"],
        "trace_sha256": sha256(trace), "browser_audit_sha256": sha256(log),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.run, args.cells, args.case), indent=2))
