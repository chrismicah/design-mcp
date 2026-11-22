"""Write anonymous browser-task specifications for the existing live critic runner."""

import argparse
import json
from pathlib import Path

from preflight import EXPECTED

HERE = Path(__file__).resolve().parent
TASKS = {
    "social-lighting": (
        "You are a theatre producer considering Blackout Lab. Use the keyboard to select Flood, "
        "verify its name and blue backlight description, and look at how light falls on the stage. "
        "Then switch to Static and check the name, hard white side light, visible change, and focus. "
        "Move focus once and check whether you can still identify the selected cue. "
        "Capture -before on entry, -after with Flood selected, and use Static for the edge action."
    ),
    "social-river": (
        "You are a resident checking local crossings. Use the keyboard to jump directly to 6 m. "
        "Verify the path, ferry and footbridge closures and compare the visible water height with the text. "
        "Check whether the complete result is readable within the first mobile viewport. "
        "Then set 2 m and check that the list correctly shows only the path closure. Capture -before on "
        "entry, -after at 6 m, and use 2 m for the edge action."
    ),
    "social-permit": (
        "Use the keyboard to try submitting without either answer. Verify how the missing answers are "
        "explained and where focus goes. Then enter the fictional name Jamie and choose Elm. Verify the "
        "confirmation includes that name and the room. Capture -before on entry, -after with the validation "
        "visible, and use a corrected submission for the edge action."
    ),
}


def write_specs(out):
    briefs = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    arms = ["v2", "social"]
    out.mkdir(parents=True, exist_ok=True)
    for brief in briefs:
        case = brief["id"]
        spec = {
            "case": case,
            "arms": arms,
            "brief": brief["brief"],
            "task": TASKS[case],
            "directions": dict(zip(arms, EXPECTED[case], strict=True)),
            "require_unhinted_direct": True,
        }
        (out / f"{case}.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out", type=Path)
    write_specs(parser.parse_args().out)
