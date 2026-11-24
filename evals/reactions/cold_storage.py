"""Check the held-out dispatch journey from browser observations."""

import math
import re

OPTION = "require_cold_storage_journey"
ACTIVATION = {"Enter", "Space"}
SEPARATORS = str.maketrans("‐‑– ", "----")


def validate_contract(contract):
    try:
        ids = contract["ids"]
        facts = contract["facts"]
        if (not isinstance(ids, list) or len(ids) != 5 or len(set(ids)) != 5 or
                not all(re.fullmatch(r"[A-Z]+-\d+", value) for value in ids) or
                not isinstance(facts, list) or len(facts) != len(ids) or
                not all(isinstance(row, list) and row for row in facts)):
            raise ValueError
        for pattern in [contract["id_pattern"], contract["delay"], contract["deadline"], *sum(facts, [])]:
            if not isinstance(pattern, str) or not pattern or re.compile(pattern).search(""):
                raise ValueError
        if loads(" ".join(ids), contract) != tuple(ids):
            raise ValueError
    except (KeyError, TypeError, ValueError, re.error):
        raise ValueError("Invalid private dispatch evidence contract") from None


def load_id(token):
    return token.upper().translate(SEPARATORS)


def loads(text, contract):
    return tuple(dict.fromkeys(load_id(match[0]) for match in re.finditer(contract["id_pattern"], text, re.I)))


def full_queue(state, contract):
    text = state["rendered_text"]
    ids = contract["ids"]
    if set(loads(text, contract)) != set(ids):
        return False
    matches = list(re.finditer(contract["id_pattern"], text, re.I))
    facts_by_id = dict(zip(ids, contract["facts"]))
    rows = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        load = load_id(match[0])
        if all(re.search(fact, text[match.end():end], re.IGNORECASE) for fact in facts_by_id[load]):
            rows.append(load)
    return list(dict.fromkeys(rows)) == ids


def deadline_visible(state, contract):
    text = state["viewport_text"]
    for match in re.finditer(contract["deadline"], text, re.IGNORECASE):
        nearby = text[max(0, match.start() - 55):match.end() + 32]
        if contract["ids"][1] in loads(nearby, contract) or re.search(r"\b(?:depart\w*|leaves?|countdown|due)\b", nearby, re.I):
            return True
    return False


def focused_queue(state, contract):
    ids = loads(state["rendered_text"], contract)
    urgent, next_load = contract["ids"][:2]
    if urgent not in ids or not set(ids) <= {urgent, next_load}:
        return False
    text = state["viewport_text"]
    return any(load_id(match[0]) == urgent and re.search(contract["delay"], text[match.end():match.end() + 70], re.I)
               for match in re.finditer(contract["id_pattern"], text, re.I))


def observation(row, field="journey"):
    record = row.get("observation", {}).get(field)
    assert isinstance(record, dict), "Missing cold-storage browser observation"
    assert record.get("truncated") is False, "Incomplete cold-storage text observation"
    assert all(isinstance(record.get(key), str) for key in ("rendered_text", "viewport_text"))
    point = record.get("scroll")
    assert isinstance(point, list) and len(point) == 2 and all(type(n) in (int, float) and math.isfinite(n) for n in point)
    assert "focus" in record
    focus = record["focus"]
    assert focus is None or (isinstance(focus, dict) and all(type(focus.get(key)) is bool
            for key in ("hittable", "at_anchor", "enabled", "visible")))
    return record


def usable_focus(state, *, at_anchor=False):
    focus = state["focus"]
    return bool(focus and focus["visible"] and focus["hittable"] and focus["enabled"] and
                (not at_anchor or focus["at_anchor"]))


def activations(rows):
    return [row for row in rows if row["op"] == "act" and row["action"] == "key" and row["value"] in ACTIVATION]


def audit_journey(rows, before, focused, after, contract):
    """Separate an observed task failure from a missing or interrupted recording."""
    assert 0 <= before < focused < after < len(rows), "Cold-storage captures are out of order"
    assert all(row.get("status") != "error" and row.get("action") != "reload" for row in rows), "Interrupted cold-storage visit"
    initial, opened, restored = (observation(rows[i]) for i in (before, focused, after))
    opening = activations(rows[before + 1:focused])
    reversing = activations(rows[focused + 1:after])
    assert len(opening) == 1 and len(reversing) <= 1, "Record one keyboard attempt per cold-storage phase"
    first = opening[0]
    prior = observation(first, "journey_before")
    entered = observation(first)
    reversal = reversing[0] if reversing else None
    reversal_prior = observation(reversal, "journey_before") if reversal else None
    returned = observation(reversal) if reversal else None
    checks = {
        "original_facts": full_queue(initial, contract) and full_queue(prior, contract),
        "entered_focus": usable_focus(prior) and all(focused_queue(frame, contract) for frame in (entered, opened)),
        "deadline_visible": all(deadline_visible(frame, contract) for frame in (initial, entered, opened)),
        "same_position_reversal": bool(reversal_prior and usable_focus(reversal_prior, at_anchor=True) and
                                       prior["scroll"] == entered["scroll"] == reversal_prior["scroll"]),
        "restored_facts": bool(returned and all(full_queue(frame, contract) for frame in (returned, restored))),
        "restored_focus": bool(returned and usable_focus(returned, at_anchor=True) and usable_focus(restored, at_anchor=True)),
    }
    if reversal:
        assert not any(row["op"] == "act" for row in rows[rows.index(reversal, focused + 1) + 1:after]), (
            "Capture the restored state before another input")
    if all(checks.values()):
        recovery = [row for row in rows[after + 1:] if row["op"] == "act"]
        assert recovery, "Cold-storage recovery was not attempted"
        repeat = activations(recovery)
        assert len(repeat) <= 2, "Record one activation and one reversal in recovery"
        checks["recovery"] = False
        if len(repeat) == 2 and repeat[0] is recovery[0]:
            second_open, second_reverse = repeat
            repeat_prior = observation(second_open, "journey_before")
            repeat_focus = observation(second_open)
            repeat_reverse = observation(second_reverse, "journey_before")
            repeat_return = observation(second_reverse)
            checks["recovery"] = (usable_focus(repeat_prior, at_anchor=True) and focused_queue(repeat_focus, contract) and
                                  deadline_visible(repeat_focus, contract) and usable_focus(repeat_reverse, at_anchor=True) and
                                  repeat_prior["scroll"] == repeat_focus["scroll"] == repeat_reverse["scroll"] and
                                  full_queue(repeat_return, contract) and usable_focus(repeat_return, at_anchor=True))
    return {"passed": all(checks.values()), "checks": checks}
