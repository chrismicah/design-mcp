"""Bind a reaction-pilot ballot to independent live inputs and original PNGs."""

import argparse
import base64
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import struct

from cold_storage import OPTION, audit_journey

HEIGHTS = {1440: 900, 390: 844}
WEIGHTS = {"coherence": "0.30", "originality": "0.30", "craft": "0.20", "usability": "0.20"}
ACTIVATION = {"Enter", "Space"}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_jsonl(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def screenshot(run, page, width, suffix, captures, calls):
    label = f"{page}-{width}-{suffix}"
    assert label in captures, f"Missing original capture {label}"
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


def audit(run, cells, case, spec=None):
    trace = (run / "critic.jsonl").read_bytes()
    log = (run / "captures/audit.jsonl").read_bytes()
    events, rows = read_jsonl(trace), read_jsonl(log)
    key = json.loads((run / "sealed-key.json").read_bytes())
    settings = json.loads((run / "driver-config.json").read_bytes())
    journey = bool(spec and spec.get(OPTION))
    assert settings.get("observe_journey", False) is journey
    expected_arms = set(spec["arms"]) if spec else {"plain", "design-mcp"}
    assert settings["original_capture"] is True and set(settings["pages"]) == set(key) == set("ABC"[:len(expected_arms)])
    assert {value["arm"] for value in key.values()} == expected_arms
    browser = (run / "browser-version.txt").read_text().strip()
    if spec:
        from benchmark_input import benchmark_cells

        assert spec == json.loads((run / "benchmark-spec.json").read_bytes())
        assert spec.get("browser", browser) == browser
        verified = benchmark_cells(cells, spec)
    builder_threads = set()
    for entry in key.values():
        cell = cells / case / entry["arm"]
        if spec:
            receipt, html = verified[entry["arm"]]
        else:
            receipt = json.loads((cell / "receipt.json").read_bytes())
            html = (cell / "index.html").read_bytes()
        assert receipt["html_sha256"] == entry["html_sha256"] == sha256(html)
        assert receipt["thread_id"] == entry["thread_id"]
        builder_threads.add(entry["thread_id"])
    threads = [event["thread_id"] for event in events if event["type"] == "thread.started"]
    completed = [event for event in events if event["type"] == "turn.completed"]
    assert len(builder_threads) == len(expected_arms) and len(threads) == len(completed) == 1
    assert threads[0] not in builder_threads and completed[0].get("usage")
    items = [event["item"] for event in events if event["type"] == "item.completed"]
    assert all(item["type"] in {"agent_message", "reasoning", "mcp_tool_call"} for item in items)
    calls = [item for item in items if item["type"] == "mcp_tool_call"]
    allowed = {"open_view", "act", "capture"}
    assert all(item["server"] == "review" and item["tool"] in allowed for item in calls)
    calls = [item for item in calls if item["status"] == "completed"]
    last_message = max(index for index, item in enumerate(items) if item["type"] == "agent_message")
    if journey:
        assert all(item["type"] != "mcp_tool_call" for item in items[last_message + 1:]), "Record the journey before submitting a ballot"
    reply = items[last_message]["text"]
    fenced = re.fullmatch(r"\s*```json\s*(.*?)\s*```\s*", reply, re.DOTALL)
    ballot = json.loads(fenced[1] if fenced else reply)
    screens = ballot["screens"]
    required = {f"{page}-{width}" for page in key for width in HEIGHTS}
    assert set(screens) <= required
    if spec:
        assert set(screens) == required, "A complete benchmark ballot requires every arm and viewport"
    captures = indexed_captures(rows)
    for label, verdict in screens.items():
        page, width_text = label.split("-")
        width = int(width_text)
        endpoint = settings["pages"][page]
        before, first = screenshot(run, page, width, "before", captures, calls)
        after, last = screenshot(run, page, width, "after", captures, calls)
        assert before < after, label
        opened_index = next(index for index in range(before - 1, -1, -1) if rows[index]["op"] == "open_view")
        opened = rows[opened_index]
        assert opened["page_id"] == page and opened["width"] == width, label
        phase = rows[before:after + 1]
        assert all(row["op"] != "open_view" and row["page_id"] == page for row in phase), label
        observed = [row for row in phase if row.get("observation")]
        assert all(row["observation"]["url"] == endpoint for row in observed), label
        actions = [row for row in observed if row["op"] == "act"]
        assert any(row["action"] == "key" and row["value"] in ACTIVATION for row in actions), label
        edge = edge_actions(rows, after)
        assert (journey or edge) and all(row["page_id"] == page and row["observation"]["url"] == endpoint for row in edge), label
        if journey:
            assert not any(row["op"] == "act" for row in rows[opened_index + 1:before]), label
            focused, focus_image = screenshot(run, page, width, "focused", captures, calls)
            following = next((offset for offset, row in enumerate(rows[after + 1:], after + 1)
                              if row["op"] == "open_view"), len(rows))
            visit = rows[before:following]
            assert all(row["page_id"] == page and row["observation"]["url"] == endpoint and
                       row["observation"]["width"] == width for row in visit), label
            checked = audit_journey(visit, 0, focused - before, after - before, spec["journey_facts"])
            assert type(verdict.get("deadline_readable")) is bool, f"Missing focused screenshot verdict for {label}"
            checked["checks"]["deadline_readable_in_screenshot"] = verdict["deadline_readable"]
            checked["passed"] = all(checked["checks"].values())
            verdict["journey"] = checked
            verdict["focused"] = focus_image
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
        **ballot, "case": case, "verified_screens": len(screens), "required_screens": len(required),
        "browser": browser,
        "evaluator_thread": threads[0], "usage": completed[0]["usage"],
        "trace_sha256": sha256(trace), "browser_audit_sha256": sha256(log),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    study = parser.add_mutually_exclusive_group(required=True)
    study.add_argument("--case")
    study.add_argument("--benchmark-spec", type=Path)
    args = parser.parse_args()
    spec = None
    if args.benchmark_spec:
        from benchmark_input import load_spec

        spec = load_spec(args.benchmark_spec)
        args.case = spec["case"]
    print(json.dumps(audit(args.run, args.cells, args.case, spec), indent=2))
