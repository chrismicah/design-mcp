import copy

import pytest

from cold_storage import audit_journey, deadline_visible, full_queue, validate_contract


BOARD = """GX-111 | 23 min late | Door 7
GX-122 | Door 2 | Leaves in nine minutes
GX-133 | Loading | Door 3
GX-144 | Staged | Door 5
GX-155 | Ready | Door 6"""
FOCUSED = "GX-111 | 23 min late | Door 7\nNext departure in 9 min"
CONTRACT = {
    "ids": ["GX-111", "GX-122", "GX-133", "GX-144", "GX-155"],
    "id_pattern": r"\bGX[-‐‑– ]\d+\b",
    "delay": r"\b23\s*min",
    "deadline": r"\b(?:9|nine)\s*min",
    "facts": [[r"\bdoor\s*7\b", r"\b23\s*min", r"\blate\b"],
              [r"\bdoor\s*2\b", r"\b(?:9|nine)\s*min"], [r"\bdoor\s*3\b", r"\bloading\b"],
              [r"\bdoor\s*5\b", r"\bstaged\b"], [r"\bdoor\s*6\b", r"\bready\b"]],
}
FOCUS = {"center": [49, 604], "hittable": True, "visible": True, "enabled": True, "at_anchor": True}


def state(text, focus=FOCUS):
    return {"rendered_text": text, "viewport_text": text, "truncated": False,
            "focus": copy.deepcopy(focus), "scroll": [0, 0]}


def capture(text, focus=FOCUS):
    return {"op": "capture", "observation": {"journey": state(text, focus)}}


def key(before, after, value="Enter"):
    return {"op": "act", "action": "key", "value": value,
            "observation": {"journey_before": state(before), "journey": state(after)}}


@pytest.fixture
def trail():
    return [capture(BOARD, None), key(BOARD, FOCUSED), capture(FOCUSED), key(FOCUSED, BOARD, "Space"),
            capture(BOARD), key(BOARD, FOCUSED), key(FOCUSED, BOARD)]


def test_journey_uses_observed_geometry_and_facts_not_control_names(trail):
    trail[1]["observation"]["focus"] = {"label": "Undo focus"}
    trail[3]["observation"]["focus"] = {"label": "Inspect exception"}
    trail[1]["observation"]["journey_before"]["focus"]["at_anchor"] = False
    assert audit_journey(trail, 0, 2, 4, CONTRACT)["passed"]


@pytest.mark.parametrize("position, phase, field, bad, check", [
    (3, "journey", "rendered_text", BOARD.replace("GX-155", "GX-166"), "restored_facts"),
    (3, "journey", "rendered_text", BOARD.replace("Door 6", "Door 9"), "restored_facts"),
    (3, "journey_before", "focus", {**FOCUS, "at_anchor": False}, "same_position_reversal"),
    (3, "journey_before", "scroll", [0, 21], "same_position_reversal"),
    (3, "journey", "focus", None, "restored_focus"),
    (1, "journey", "viewport_text", "GX-111 | 23 min late | Door 7", "deadline_visible"),
    (5, "journey", "rendered_text", BOARD, "recovery"),
])
def test_complete_failure_trace_remains_scoreable(trail, position, phase, field, bad, check):
    trail[position]["observation"][phase][field] = bad
    evidence = audit_journey(trail, 0, 2, 4, CONTRACT)
    assert not evidence["passed"]
    assert [name for name, value in evidence["checks"].items() if not value] == [check]


def test_an_unrelated_key_is_not_a_reversal(trail):
    trail[3] = {"op": "act", "action": "key", "value": "Tab"}
    evidence = audit_journey(trail, 0, 2, 4, CONTRACT)
    assert not evidence["passed"] and not evidence["checks"]["same_position_reversal"]


def test_a_later_tab_cannot_repair_missing_focus_evidence(trail):
    trail.insert(4, {"op": "act", "action": "key", "value": "Tab"})
    with pytest.raises(AssertionError, match="before another input"):
        audit_journey(trail, 0, 2, 5, CONTRACT)


def test_missing_observation_blocks_instead_of_scoring_as_failure(trail):
    del trail[1]["observation"]["journey_before"]
    with pytest.raises(AssertionError, match="Missing cold-storage browser observation"):
        audit_journey(trail, 0, 2, 4, CONTRACT)


def test_missing_recovery_blocks_a_successful_primary_journey(trail):
    with pytest.raises(AssertionError, match="recovery was not attempted"):
        audit_journey(trail[:5], 0, 2, 4, CONTRACT)


def test_wrong_order_and_unrelated_time_do_not_pass():
    assert not full_queue(state(BOARD.replace("GX-133", "GX-144").replace("GX-144 | Staged", "GX-133 | Staged")), CONTRACT)
    assert not deadline_visible(state("GX-111 | 23 min late | Door 7\nLast dispatch took nine minutes"), CONTRACT)


def test_next_departure_summary_can_precede_the_queue():
    assert full_queue(state("Next departure: GX-122 in nine minutes\n" + BOARD), CONTRACT)

def test_contract_rejects_a_pattern_that_cannot_match_the_private_identifiers():
    validate_contract(CONTRACT)
    with pytest.raises(ValueError, match="Invalid private dispatch evidence contract"):
        validate_contract({**CONTRACT, "id_pattern": r"ZZ-\d+"})
