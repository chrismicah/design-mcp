import base64
import json
import struct

import pytest

from audit_review import audit, HEIGHTS
from live_review import PACKAGE_COMMIT, benchmark_cells, critic_prompt, eligible_pair, generate, load_spec
from cold_storage import OPTION
from test_cold_storage import BOARD, CONTRACT, FOCUSED, state


@pytest.fixture
def pair(tmp_path):
    case = "dashboard-clear"
    for arm in ("plain", "design-mcp"):
        cell = tmp_path / case / arm
        cell.mkdir(parents=True)
        contents = {"index.html": b"<h1>Load board</h1>", "client.jsonl": b"{}", "prompt.txt": b"calmer"}
        for name, data in contents.items():
            (cell / name).write_bytes(data)
        (cell / "receipt.json").write_text(json.dumps({
            "case": case, "arm": arm, "source_commit": PACKAGE_COMMIT if arm == "design-mcp" else None,
            "client": "codex-cli 0.170.0", "model": "generator", "effort": "max", "reaction_number": 1,
            "thread_id": f"{arm}-session", "status": "passed", "usage": {"input_tokens": 10},
            "html_sha256": generate.sha256(contents["index.html"]),
            "trace_sha256": generate.sha256(contents["client.jsonl"]),
            "prompt_sha256": generate.sha256(contents["prompt.txt"]),
        }))
    return tmp_path, case


def test_matching_pair_serves_the_verified_bytes(pair):
    labeled = eligible_pair(*pair)
    assert set(labeled) == {"A", "B"}
    assert {receipt["arm"] for receipt, _ in labeled.values()} == {"plain", "design-mcp"}
    assert all(html == b"<h1>Load board</h1>" for _, html in labeled.values())


def test_pair_with_a_different_reaction_round_is_ineligible(pair):
    root, case = pair
    receipt_path = root / case / "plain" / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["reaction_number"] = 2
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="reaction_number"):
        eligible_pair(*pair)


def test_pair_with_html_changed_after_generation_is_ineligible(pair):
    root, case = pair
    (root / case / "design-mcp" / "index.html").write_text("<h1>Different board</h1>")
    with pytest.raises(ValueError, match="design-mcp/index.html"):
        eligible_pair(*pair)


@pytest.fixture
def benchmark(tmp_path, request):
    spec = {"case": "cold-storage", "brief": "A worklist.", "task": "Focus and restore all rows.",
            "arms": ["none", "router", "candidate"], "directions": {"router": "exception-first",
                                                                "candidate": "exception-first"}}
    unhinted = getattr(request, "param", False)
    if unhinted:
        spec["require_unhinted_direct"] = True
    prompt = generate.generation_prompt(spec["brief"], unhinted)
    usage = {"output_tokens": 10}
    for arm in spec["arms"]:
        root = tmp_path / spec["case"] / arm
        root.mkdir(parents=True)
        html = f"<body>{arm}</body>\n"
        events = [{"type": "thread.started", "thread_id": f"{arm}-session"}]
        if arm != "none":
            events.append({"type": "item.completed", "item": {
                "type": "mcp_tool_call", "server": "design-mcp", "tool": "direct", "status": "completed",
                "arguments": {"brief": spec["brief"]},
                "result": {"structured_content": {"direction": {"id": "exception-first"}}}}})
        events.extend([
            {"type": "item.completed", "item": {
                "type": "agent_message", "text": f"```html\n{html}```"}},
            {"type": "turn.completed", "usage": usage},
        ])
        trace = "".join(json.dumps(event) + "\n" for event in events)
        for name, data in (("index.html", html), ("client.jsonl", trace), ("prompt.txt", prompt)):
            (root / name).write_text(data)
        (root / "receipt.json").write_text(json.dumps({
            "case": spec["case"], "arm": arm, "status": "passed", "usage": usage,
            "client": "test", "model": "test", "effort": "max",
            "require_unhinted_direct": unhinted,
            "html_sha256": generate.sha256(html.encode()), "trace_sha256": generate.sha256(trace.encode()),
            "prompt_sha256": generate.sha256(prompt.encode()),
        }))
    return tmp_path, spec


def set_direct_arguments(root, spec, arm, arguments):
    cell = root / spec["case"] / arm
    trace_path = cell / "client.jsonl"
    events = [json.loads(line) for line in trace_path.read_text().splitlines()]
    (direct,) = (event["item"] for event in events if event.get("item", {}).get("tool") == "direct")
    direct["arguments"] = arguments
    raw = "".join(json.dumps(event) + "\n" for event in events).encode()
    trace_path.write_bytes(raw)
    receipt_path = cell / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    receipt["trace_sha256"] = generate.sha256(raw)
    receipt_path.write_text(json.dumps(receipt))


@pytest.mark.parametrize("benchmark", [True], indirect=True)
@pytest.mark.parametrize("arguments", [
    {"brief": "A worklist.", "surface": "dashboard"},
    {"brief": "A worklist.", "avoid": ["object-hero"]},
    {"brief": "A worklist. Use the exception-first direction."},
    {},
])
def test_unhinted_preflight_checks_arguments_even_with_the_right_reply(benchmark, arguments):
    root, spec = benchmark
    assert list(benchmark_cells(root, spec)) == spec["arms"]
    set_direct_arguments(root, spec, "candidate", arguments)
    with pytest.raises(ValueError, match="hinted-or-changed-direct"):
        benchmark_cells(root, spec)


@pytest.mark.parametrize("benchmark", [True], indirect=True)
def test_unhinted_spec_cannot_omit_a_treatment_direction(benchmark):
    root, spec = benchmark
    spec["directions"].pop("candidate")
    spec_path = root / "spec.json"
    spec_path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="direction ID for each"):
        load_spec(spec_path)


def test_preflight_replays_all_three_arms_and_keeps_prompt_blind(benchmark):
    root, spec = benchmark
    spec_path = root / "spec.json"
    spec_path.write_text(json.dumps(spec))
    verified = benchmark_cells(root, load_spec(spec_path))
    assert list(verified) == spec["arms"]
    assert len({value[0]["thread_id"] for value in verified.values()}) == 3
    prompt = critic_prompt(None, spec)
    assert "C-390" in prompt and all(arm not in prompt for arm in spec["arms"])


@pytest.mark.parametrize("mutant,message", [
    ("html", "hash mismatch"),
    ("prompt", "hash mismatch"),
    ("shell", "shell policy"),
    ("direction", "unexpected-design-direction"),
    ("session", "distinct generator session"),
])
def test_preflight_rejects_noncomparable_cells(benchmark, mutant, message):
    root, spec = benchmark
    cell = root / spec["case"] / "candidate"
    receipt_path = cell / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    if mutant == "html":
        (cell / "index.html").write_text("<body>Different build</body>")
    elif mutant == "prompt":
        (cell / "prompt.txt").write_text("Changed brief")
    elif mutant == "shell":
        receipt["shell_tool"] = False
    elif mutant == "direction":
        spec["directions"]["candidate"] = "object-hero"
    elif mutant == "session":
        trace = cell / "client.jsonl"
        raw = trace.read_bytes().replace(b"candidate-session", b"router-session")
        trace.write_bytes(raw)
        receipt["trace_sha256"] = generate.sha256(raw)
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match=message):
        benchmark_cells(root, spec)


@pytest.mark.parametrize("benchmark", [True], indirect=True)
@pytest.mark.parametrize("journey", [False, True])
def test_three_arm_audit_requires_six_views(benchmark, journey):
    root, spec = benchmark
    if journey:
        spec.update({OPTION: True, "journey_facts": CONTRACT})
    eligible = benchmark_cells(root, spec)
    key = {label: {field: receipt[field] for field in ("arm", "thread_id", "html_sha256")}
           for label, (receipt, _) in zip("ABC", eligible.values(), strict=True)}
    run = root / "review"
    captures = run / "captures"
    captures.mkdir(parents=True)
    pages = {label: f"http://127.0.0.1:{8000 + index}/index.html"
             for index, label in enumerate(key)}
    settings = {"original_capture": True, "pages": pages, "observe_journey": journey}
    for name, value in (("sealed-key.json", key), ("benchmark-spec.json", spec), ("driver-config.json", settings)):
        (run / name).write_text(json.dumps(value))
    (run / "browser-version.txt").write_text("Chrome/158.0.8127.36\n")
    trace = [{"type": "thread.started", "thread_id": "independent-critic"}]
    rows = []
    ballot = {"screens": {}}
    for page, url in pages.items():
        for width, height in HEIGHTS.items():
            view = f"{page}-{width}"
            observation = {"url": url, "width": width, "layout_width": width}
            rows.append({"op": "open_view", "page_id": page, "width": width})
            phases = (("before", BOARD, FOCUSED), ("focused", FOCUSED, BOARD), ("after", BOARD, FOCUSED)) if journey else (
                ("before", BOARD, FOCUSED), ("after", FOCUSED, BOARD))
            for suffix, old, new in phases:
                label = f"{view}-{suffix}"
                filename = f"{label}.png"
                raw = b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + struct.pack(">II", width, height) + label.encode()
                (captures / filename).write_bytes(raw)
                captured = {**observation, "journey": state(old)} if journey else observation
                rows.append({"op": "capture", "page_id": page, "label": label, "path": filename,
                             "observation": captured, "sha256": generate.sha256(raw)})
                encoded = base64.b64encode(raw).decode()
                trace.append({"type": "item.completed", "item": {
                    "type": "mcp_tool_call", "server": "review", "tool": "capture", "status": "completed",
                    "id": label, "arguments": {"label": label},
                    "result": {"content": [{"type": "image", "mimeType": "image/png", "data": encoded}]},
                }})
                inputs = [(old, new)]
                if journey and suffix == "after":
                    inputs.append((new, old))
                for start, end in inputs:
                    result = {**observation, "journey_before": state(start), "journey": state(end)} if journey else observation
                    rows.append({"op": "act", "page_id": page, "action": "key", "value": "Enter",
                                 "observation": result})
            ballot["screens"][view] = {
                "coherence": 8, "originality": 8, "craft": 8, "usability": 8,
                "primary_action": {"input": "Enter", "expected": "Focus", "observed": "Focused"},
                "edge_observation": "Restored", "strength": "Readable", "weakness": "Crowded", "repair": "Group",
            }
    (captures / "audit.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))

    def write_trace():
        complete = trace + [
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(ballot)}},
            {"type": "turn.completed", "usage": {"output_tokens": 10}},
        ]
        (run / "critic.jsonl").write_text("".join(json.dumps(event) + "\n" for event in complete))

    write_trace()
    result = audit(run, root, spec["case"], spec)
    assert result["verified_screens"] == result["required_screens"] == 6
    assert result["screens"]["C-390"]["arm"] == "candidate"
    if journey:
        assert all(screen["journey"]["passed"] for screen in result["screens"].values())
        assert "-focused" in critic_prompt(None, spec)
        without_focus = [row for row in rows if row.get("label") != "C-390-focused"]
        (captures / "audit.jsonl").write_text("".join(json.dumps(row) + "\n" for row in without_focus))
        with pytest.raises(AssertionError, match="Missing original capture C-390-focused"):
            audit(run, root, spec["case"], spec)
    ballot["screens"].pop("C-390")
    write_trace()
    with pytest.raises(AssertionError, match="every arm and viewport"):
        audit(run, root, spec["case"], spec)
