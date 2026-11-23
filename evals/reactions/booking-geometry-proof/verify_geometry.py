"""Check which booking frame changes and whether its result is immediately visible."""
import json
from pathlib import Path
import sys

WIDTHS = (1440, 390, 320)
TASK_CHECKS = ("facts", "days", "fits_width", "reduced_motion_preference", "keyboard_booking", "pointer_booking")
PHASES = ("before", "keyboard-friday", "pointer-tuesday")


def rows(receipt, arm):
    observed = {}
    for screen in receipt["pages"][arm]["screens"]:
        width = screen["width"]
        assert width in WIDTHS and width not in observed, (arm, width)
        frames = {frame["phase"]: frame for frame in screen["evidence"]}
        observed[width] = (screen["checks"], frames)
        assert all(phase in frames for phase in PHASES), (arm, width)
    assert set(observed) == set(WIDTHS), arm
    return observed


def compare(receipt):
    current = rows(receipt, "initial")
    calmer = rows(receipt, "calmer")
    widths = {}
    for width in WIDTHS:
        current_checks, baseline = current[width]
        revised_checks, revised = calmer[width]
        previous_heading = baseline["before"]
        revised_heading = revised["before"]
        before_px = float(previous_heading["size"].removesuffix("px"))
        after_px = float(revised_heading["size"].removesuffix("px"))
        checks = {
            "both_booking_journeys_pass": all(checks[name] for checks in (current_checks, revised_checks) for name in TASK_CHECKS),
            "visible_change": all(baseline[phase]["sha256"] != revised[phase]["sha256"] for phase in PHASES),
            "heading_legible_and_quieter": 0 < after_px < before_px
                and revised_heading["font"] == previous_heading["font"]
                and revised_heading["color"] == previous_heading["color"],
            "all_choice_targets_at_least_44px": all(
                min(control["w"], control["h"]) >= 44
                for phase in PHASES for control in revised[phase]["controls"]
            ),
            "summary_visible_immediately_after_selection": all(
                revised[phase]["summaryInView"] for phase in PHASES[1:]
            ),
        }
        widths[width] = {
            "checks": checks,
            "heading_px": [before_px, after_px],
            "reported_summary_visible_on_friday": [
                baseline["keyboard-friday"]["summaryInView"],
                revised["keyboard-friday"]["summaryInView"],
            ],
        }
    return {"passed": all(all(width["checks"].values()) for width in widths.values()), "widths": widths}


if __name__ == "__main__":
    outcome = compare(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(outcome, indent=2))
    raise SystemExit(not outcome["passed"])
