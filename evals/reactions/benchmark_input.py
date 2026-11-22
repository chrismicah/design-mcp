"""Preflight matched benchmark cells before an independent live review."""

import json
import re

from cold_storage import OPTION, validate_contract
from pilot import generate

HASH_FIELDS = ("prompt_sha256", "html_sha256", "trace_sha256")
GENERATOR_FIELDS = ("client", "model", "effort", "shell_tool")


def control_conditions(receipt):
    return {"client": receipt["client"], "model": receipt["model"], "effort": receipt["effort"],
            "shell_tool": receipt.get("shell_tool", True)}


def load_spec(path):
    spec = json.loads(path.read_bytes())
    slug = r"[a-z0-9]+(?:-[a-z0-9]+)*"
    arms = spec["arms"]
    if (not isinstance(arms, list) or not 2 <= len(arms) <= 3
            or not all(isinstance(arm, str) and re.fullmatch(slug, arm) for arm in arms)
            or len(set(arms)) != len(arms)):
        raise ValueError("Declare two or three distinct benchmark arms")
    if not re.fullmatch(slug, spec["case"]):
        raise ValueError("Invalid benchmark case ID")
    if not all(isinstance(spec[field], str) and spec[field].strip() for field in ("brief", "task")):
        raise ValueError("The benchmark needs a generation brief and a critic task")
    directions = spec.get("directions", {})
    if (not isinstance(directions, dict) or not directions.keys() <= set(arms) - {"none", "shadcn"}
            or not all(isinstance(value, str) and re.fullmatch(slug, value) for value in directions.values())):
        raise ValueError("Expected direction IDs must refer to Design MCP arms")
    unhinted = spec.get("require_unhinted_direct", False)
    if type(unhinted) is not bool or (unhinted and directions.keys() != set(arms) - {"none"}):
        raise ValueError("An unhinted comparison requires a direction ID for each Design MCP arm")
    journey = spec.get(OPTION, False)
    if type(journey) is not bool or (journey and (spec["case"] != "cold-storage" or not unhinted)):
        raise ValueError("The dispatch journey requires the unhinted cold-storage comparison")
    if journey:
        validate_contract(spec.get("journey_facts"))
    if "browser" in spec and not re.fullmatch(r"Chrome/\d+\.\d+\.\d+\.\d+", spec["browser"]):
        raise ValueError("Pin the expected browser as Chrome/major.minor.build.patch")
    pins = spec.get("pinned_controls", {})
    if not isinstance(pins, dict) or not pins.keys() <= set(arms):
        raise ValueError("Pin only declared archived control arms")
    for arm, pin in pins.items():
        if (not isinstance(pin, dict) or set(pin) != set(HASH_FIELDS + GENERATOR_FIELDS)
                or not all(isinstance(pin[key], str) and re.fullmatch(r"[0-9a-f]{64}", pin[key]) for key in HASH_FIELDS)
                or not all(isinstance(pin[key], str) and pin[key].strip() for key in GENERATOR_FIELDS[:-1])
                or type(pin["shell_tool"]) is not bool):
            raise ValueError(f"Invalid immutable control pin for {arm}")
    return spec


def benchmark_cells(cells, spec, *, pinned_only=False):
    case = spec["case"]
    unhinted = spec.get("require_unhinted_direct", False)
    prompt = generate.generation_prompt(spec["brief"], unhinted).encode()
    verified = {}
    identity = None
    threads = set()
    pins = spec.get("pinned_controls", {})
    if pinned_only and not pins:
        raise ValueError("Declare the archived controls before preflighting them")
    arms = [arm for arm in spec["arms"] if not pinned_only or arm in pins]
    for arm in arms:
        cell = cells / case / arm
        receipt = json.loads((cell / "receipt.json").read_bytes())
        if (receipt["case"], receipt["arm"], receipt["status"]) != (case, arm, "passed"):
            raise ValueError(f"Ineligible generation receipt for {case}/{arm}")
        if receipt.get("require_unhinted_direct", False) != unhinted:
            raise ValueError(f"Unhinted direct policy differs for {case}/{arm}")
        conditions = control_conditions(receipt)
        if arm in pins and {**conditions, **{key: receipt[key] for key in HASH_FIELDS}} != pins[arm]:
            raise ValueError(f"Archived control differs from its pin for {case}/{arm}")
        if identity is not None and conditions != identity:
            raise ValueError(f"Generator or shell policy differs for {case}/{arm}")
        identity = conditions
        trace = cell / "client.jsonl"
        html = (cell / "index.html").read_bytes()
        if (prompt != (cell / "prompt.txt").read_bytes() or generate.sha256(prompt) != receipt["prompt_sha256"]
                or generate.sha256(html) != receipt["html_sha256"]
                or generate.sha256(trace.read_bytes()) != receipt["trace_sha256"]):
            raise ValueError(f"Generation hash mismatch for {case}/{arm}")
        events = generate.read_trace(trace)
        server, tools, items = "design-mcp", "direct", ()
        if arm == "shadcn":
            config = json.loads((generate.BASE_DIR / "shadcn-maintenance.json").read_bytes())
            server, tools, items = config["name"], config["expected_tools"], config["required_shadcn_items"]
        direction = spec.get("directions", {}).get(arm)
        parsed, reply = generate.parse_cell(events, expect_mcp=arm != "none", server_name=server,
                                           expected_tool=tools, expected_direction=direction,
                                           required_shadcn_items=items,
                                           expected_direct_brief=spec["brief"] if unhinted and arm != "none" else None)
        if (parsed["status"] != "passed" or not parsed["usage"] or parsed["usage"] != receipt["usage"]
                or reply is None or reply.encode() != html):
            raise ValueError(f"Generation trace failed replay for {case}/{arm}: {parsed['status']}")
        sessions = [event["thread_id"] for event in events if event["type"] == "thread.started"]
        if len(sessions) != 1 or not sessions[0] or sessions[0] in threads:
            raise ValueError(f"Expected a distinct generator session for {case}/{arm}")
        threads.add(sessions[0])
        verified[arm] = ({**receipt, "thread_id": sessions[0]}, html)
    return verified
