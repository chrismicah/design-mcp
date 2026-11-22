"""Answer a bounded keyboard-focus question from an audited live browser trace."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ACTIVATE = {"Enter", "Space"}
RECOVER = ACTIVATE | {"Escape"}


def focus(row):
    state = row.get("observation", {}).get("focus", {})
    if not (state.get("visible") is True and state.get("document_focused") is True
            and state.get("embedded") is False):
        return None
    label = " ".join((state.get("label") or "").split())
    tag = state.get("tag")
    return (tag, label) if tag and label else None


def key_is(row, choices):
    return row["op"] == "act" and row.get("action") == "key" and row.get("value") in choices


def returned_focus(rows, screen):
    """Return an observed control name when an action moves focus and recovery returns it.

    The answer describes the visible tag and label. This trace has no DOM node identity.
    """
    before_label, after_label = (f"{screen}-{name}" for name in ("before", "after"))
    captures = {row["label"]: index for index, row in enumerate(rows)
                if row["op"] == "capture" and row.get("observation")}
    before, after = captures.get(before_label), captures.get(after_label)
    if before is None or after is None or before >= after:
        return None
    origin = rows[before]
    page, _, width = screen.partition("-")
    if (not width.isdecimal() or origin.get("page_id") != page
            or origin["observation"].get("width") != int(width) or not origin["observation"].get("url")):
        return None
    end = next((i for i in range(after + 1, len(rows)) if rows[i]["op"] == "open_view"), len(rows))
    view = rows[before:end]
    dimensions = ("url", "width", "height")
    if any(not row.get("observation") or row.get("page_id") != origin["page_id"] or
           any(row["observation"].get(k) != origin["observation"].get(k) for k in dimensions)
           for row in view):
        return None
    launch = next((i for i in range(before + 1, after) if key_is(rows[i], ACTIVATE)), None)
    recover = next((i for i in range(after + 1, end) if key_is(rows[i], RECOVER)), None)
    if launch is None or recover is None:
        return None
    start, moved, restored = (focus(rows[i]) for i in (launch - 1, launch, recover))
    if start is None or start[0] not in {"button", "a"} or moved is None or moved == start or restored != start:
        return None
    return {"tag": restored[0], "label": restored[1],
            "launch_key": rows[launch]["value"], "recovery_key": rows[recover]["value"]}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def replay(run, ballot_path):
    raw = (run / "captures/audit.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    ballot_raw = ballot_path.read_bytes()
    ballot = json.loads(ballot_raw)
    if digest(raw) != ballot["browser_audit_sha256"]:
        raise ValueError("Browser trace does not match the audited ballot")
    answers = {}
    for screen, verdict in ballot["screens"].items():
        for state in ("before", "after"):
            capture = verdict[state]
            stored = (run / "captures" / capture["file"]).read_bytes()
            if digest(stored) != capture["sha256"]:
                raise ValueError(f"Capture does not match the audited ballot: {screen}/{state}")
        answer = returned_focus(rows, screen)
        answers[screen] = {"arm": verdict["arm"], "answer": answer}
        if answer is None:
            continue

        marker = next(i for i, row in enumerate(rows) if row.get("label") == f"{screen}-after")
        recovery = next(i for i in range(marker + 1, len(rows)) if key_is(rows[i], RECOVER))
        negatives = {}
        for name, key, value in (("invisible", "visible", False), ("embedded", "embedded", True),
                                  ("other_control", "label", "Different control")):
            variant = deepcopy(rows)
            variant[recovery]["observation"]["focus"][key] = value
            negatives[name] = returned_focus(variant, screen) is None
        variant = deepcopy(rows)
        variant[recovery]["observation"]["width"] += 1
        negatives["other_viewport"] = returned_focus(variant, screen) is None
        variant = deepcopy(rows)
        for row in variant[marker + 1:]:
            if row["op"] == "open_view":
                break
            if key_is(row, RECOVER):
                row["value"] = "Tab"
        negatives["no_recovery_input"] = returned_focus(variant, screen) is None
        if not all(negatives.values()):
            raise ValueError(f"Returned a focus answer for contradictory evidence: {screen}")
        answers[screen]["negative_controls_abstained"] = negatives
    return {
        "case": ballot["case"], "ballot_sha256": digest(ballot_raw), "browser_audit_sha256": digest(raw),
        "frontier_calls_for_focus_question": 0, "frontier_input_tokens_for_focus_question": 0,
        "views": answers,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="Archived live review run directory")
    parser.add_argument("ballot", type=Path, help="Audited full-image live ballot")
    args = parser.parse_args()
    print(json.dumps(replay(args.run, args.ballot), indent=2))


if __name__ == "__main__":
    main()
