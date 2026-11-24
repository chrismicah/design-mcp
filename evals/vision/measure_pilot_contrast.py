"""Resolve this pilot's axe contrast findings with paired rendered backgrounds."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from PIL import Image


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def luminance(rgb):
    def linearize(value):
        value = value / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    return sum(weight * linearize(value) for weight, value in zip((0.2126, 0.7152, 0.0722), rgb))


def ratio(foreground, background):
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + 0.05) / (low + 0.05)


def grain_upper_bound(rgb):
    """Worst-case white soft-light at the source illustration's 19% opacity."""
    def channel(value):
        base = value / 255
        blended = ((16 * base - 12) * base + 4) * base if base <= 0.25 else math.sqrt(base)
        return math.ceil((base * 0.81 + blended * 0.19) * 255)

    return tuple(channel(value) for value in rgb)


def resolve_sample(sample, scan, cell, width, height, source):
    foreground_meta, background_meta = sample["statePath"], sample["backgroundPath"]
    foreground_path, background_path = cell / foreground_meta["file"], cell / background_meta["file"]
    if sha(foreground_path) != foreground_meta["sha256"] or sha(background_path) != background_meta["sha256"]:
        raise ValueError("A contrast sample differs from its captured hash")
    with Image.open(foreground_path) as opened:
        original = opened.convert("RGB")
    with Image.open(background_path) as opened:
        background = opened.convert("RGB")
    if original.size != background.size or original.size != (width, height):
        raise ValueError("The contrast sample geometry differs from the capture")
    floors = {item["target"][0]: float(item["related"][0]["expectedContrastRatio"].split(":")[0])
              for item in scan["incomplete"]}
    if {row["selector"] for row in sample["elements"]} != floors.keys():
        raise ValueError("Unresolved axe elements differ from the rendered samples")
    before, behind = original.load(), background.load()
    checked = []
    for el in sample["elements"]:
        selector = el["selector"]
        if el["svg"]:
            if 'filter="url(#studio-grain)" opacity=".19"' not in source or "mix-blend-mode: soft-light" not in source:
                raise ValueError("The nominal SVG contrast bound depends on the captured grain style")
        color = tuple(map(int, re.fullmatch(r"rgb\((\d+), (\d+), (\d+)\)", el["color"]).groups()))
        effective = grain_upper_bound(color) if el["svg"] else color
        left, top, right, bottom = el["box"]
        if left < 0 or top < 0 or right > width or bottom > height or right <= left or bottom <= top:
            raise ValueError(f"Unresolved target falls outside the viewport: {selector}")
        changed = [(before[x, y], behind[x, y])
                   for y in range(math.floor(top), math.ceil(bottom))
                   for x in range(math.floor(left), math.ceil(right))
                   if max(abs(a - b) for a, b in zip(before[x, y], behind[x, y])) >= 5]
        if not changed:
            raise ValueError(f"No glyph pixels changed for {selector}")
        floor = floors[selector]
        darkest_background = min((bg for _, bg in changed), key=luminance)
        contrast = ratio(effective, darkest_background) if luminance(effective) < luminance(darkest_background) else 1.0
        visible = max(ratio(fg, bg) for fg, bg in changed)
        checked.append({"target": selector, "visible_pixels": len(changed), "declared_foreground_rgb": color,
                        "conservative_foreground_rgb": effective, "background_min_ratio": contrast,
                        "observed_peak_ratio": visible, "required_ratio": floor,
                        "passed": contrast >= floor and visible >= floor})
    return {"hashes": [foreground_meta["sha256"], background_meta["sha256"]], "targets": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("reference", type=Path, help="Original keyboard action capture archive")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    report = {"rule": "axe-core 4.14.1 color-contrast",
              "method": "Sample the background under changed glyph pixels after making unresolved text transparent. "
                        "Verify the source foreground, including a worst-case soft-light bound for SVG labels, and record "
                        "the strongest actual pixel contrast to confirm the text was visible.",
              "cases": {}}
    for case in ("landing", "mobile"):
        cell = args.archive / case / "pilot-repair"
        source = cell / "index.html"
        original = args.reference / case / "pilot-repair" / "index.html"
        render = json.loads((cell / "render.json").read_bytes())
        digest = sha(source)
        if sha(original) != digest or render["input_sha256"] != digest:
            raise ValueError(f"{case}: wrong HTML provenance")
        state_report = {}
        for key, width, height in (("1440", 1440, 900), ("390", 390, 844)):
            action = render["captures"][key]["interaction"]
            if set(action["contrast"]) != {"initial", "after"}:
                raise ValueError(f"{case}/{key}: missing contrast capture state")
            if not action["passed"] or sha(cell / f"{key}-action.png") != action["action_sha256"]:
                raise ValueError(f"{case}/{key}: invalid keyboard replay evidence")
            phases = {}
            for phase, scan in action["contrast"].items():
                summary = {"passed_nodes": scan["passedNodes"], "violations": scan["violations"]}
                if scan["incomplete"]:
                    summary["sampling"] = resolve_sample(scan["sample"], scan, cell, width, height, source.read_text())
                phases[phase] = summary
            state_report[key] = phases
        report["cases"][case] = {"html_sha256": digest, "viewports": state_report}
    report["passed"] = all(not phase["violations"] and all(target["passed"] for target in
                          phase.get("sampling", {}).get("targets", [])) for result in report["cases"].values()
                          for screen in result["viewports"].values() for phase in screen.values())
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
