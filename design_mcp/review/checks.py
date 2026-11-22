"""Local checks on normalized evidence: arithmetic on what the browser measured, with no network or model.

Each finding names the region, the problem, one concrete change and an outcome that can be tested.
An empty result means these three checks found nothing. It does not certify the design.
"""

import math

from .evidence import UNKNOWN

MIN_CONTRAST = 4.5
MIN_LARGE_TEXT_CONTRAST = 3.0
_PRIORITY = ("covered-control", "overflow", "contrast")


def _linear(channel):
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    red, green, blue = (_linear(channel) for channel in rgb[:3])
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(ink, fill):
    """WCAG contrast ratio between two opaque sRGB colors."""
    lighter, darker = sorted((luminance(ink), luminance(fill)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def composite(ink, fill):
    """The color a possibly translucent ink shows as on an opaque fill."""
    alpha = ink[3] if len(ink) == 4 else 1
    return [round(alpha * ink[index] + (1 - alpha) * fill[index]) for index in range(3)]


def suggest_ink(ink, fill, target=MIN_CONTRAST):
    """The closest color to `ink`, moving toward black or white, that reaches `target` on `fill`."""
    directions = (0, 255) if luminance(ink) <= luminance(fill) else (255, 0)
    for toward in directions:
        for step in range(256):
            candidate = [round(channel + (toward - channel) * step / 255) for channel in ink[:3]]
            if contrast_ratio(candidate, fill) >= target:
                return candidate
    return None


def hex_color(rgb):
    return "#%02x%02x%02x" % tuple(rgb[:3])


def _floor(value, places):
    scale = 10 ** places
    return math.floor(value * scale + 1e-9) / scale


def _ratio(value):
    return f"{_floor(value, 1):.1f}"


def _label(region, fallback):
    if region["name"] != UNKNOWN:
        return f"“{region['name']}”"
    if region["role"] != UNKNOWN:
        return f"the {region['role']}"
    return fallback


def _sentence(text):
    return text[:1].upper() + text[1:]


def _finding(check, frame, region, **fields):
    viewport = frame["viewport"]
    return {
        "check": check,
        "frame": frame["id"],
        "viewport": f"{viewport['width']}x{viewport['height']}",
        "region": region["id"] if region else UNKNOWN,
        "box": region["box"] if region else None,
        "preview": None,
        **fields,
    }


def _covered_control(frame):
    primary = frame["primary_control"]
    if not primary or not primary["covered_by"]:
        return None
    region = next((item for item in frame["regions"] if item["id"] == primary["region"]), None)
    if region is None:
        return None
    cover, width = primary["covered_by"], frame["viewport"]["width"]
    control = _label(region, "the main button")
    bar = f"“{cover['name']}”" if cover["name"] != UNKNOWN else f"a {cover['position']} bar"
    space = f"{cover['height_px']} px of space" if cover["height_px"] != UNKNOWN else "enough space"
    return _finding(
        "covered-control", frame, region,
        problem=_sentence(f"{bar} stays on top of {control} at {width} px wide, "
                          "so a click on the button lands on the bar instead."),
        change=f"Move {bar} off {control}, or add {space} so the button sits clear of it.",
        outcome=f"At {width} px wide, the element at the center of {control} is the button itself.",
        evidence={"covered_by": cover, "basis": primary["basis"]},
    )


def _overflow(frame):
    document, width = frame["document"], frame["viewport"]["width"]
    if UNKNOWN in (document["scroll_width"], document["client_width"]):
        return None
    extra = document["scroll_width"] - document["client_width"]
    if extra <= 1:
        return None
    offender = frame["overflow"]
    culprit = None
    if offender and offender["name"] != UNKNOWN:
        culprit = f"“{offender['name']}”"
    elif offender and offender["locator"] != UNKNOWN:
        culprit = f"the element at {offender['locator']}"
    if culprit:
        because = f" because {culprit} is wider than the screen"
        change = f"Keep {culprit} inside the screen width, for example with max-width: 100%, or let its content wrap."
    else:
        because = ""
        change = (f"Find the element that is wider than {document['client_width']} px and keep it inside the "
                  "screen width, for example with max-width: 100%.")
    return _finding(
        "overflow", frame, None,
        box=offender["box"] if offender else None,
        problem=f"The page scrolls sideways by {extra} px at {width} px wide{because}.",
        change=change,
        outcome=(f"At {width} px wide the page is as wide as the screen: scrollWidth minus clientWidth "
                 "is 1 px or less."),
        evidence={
            "scroll_width": document["scroll_width"],
            "client_width": document["client_width"],
            "locator": offender["locator"] if offender else UNKNOWN,
        },
    )


def _low_contrast(frame):
    width = frame["viewport"]["width"]
    for region in frame["regions"]:
        ink, fill, font = region["ink"], region["fill"], region["font"]
        if (not region["has_text"] or region["masked"] or region["disabled"] or region["fill_flat"] is not True
                or UNKNOWN in (ink, fill, font["size_px"]) or fill[3] < 1):
            continue
        bold = font["weight"] != UNKNOWN and font["weight"] >= 700
        large = font["size_px"] >= 24 or (bold and font["size_px"] >= 14 * 4 / 3)
        target = MIN_LARGE_TEXT_CONTRAST if large else MIN_CONTRAST
        seen = composite(ink, fill)
        ratio = contrast_ratio(seen, fill)
        if ratio >= target:
            continue
        better = suggest_ink(seen, fill, target)
        if better is None:
            continue
        label = _label(region, "this text")
        before, after, ground = hex_color(seen), hex_color(better), hex_color(fill)
        new_ratio = contrast_ratio(better, fill)
        yield ratio, _finding(
            "contrast", frame, region,
            problem=_sentence(f"{label} is hard to read at {width} px wide: its text color {before} on {ground} "
                              f"measures {_ratio(ratio)} to 1, and text this size needs at least {target:g} to 1."),
            change=f"Change the text color of {label} from {before} to {after}.",
            outcome=_sentence(f"{label} measures at least {target:g} to 1 against its background "
                              f"({_ratio(new_ratio)} to 1 with {after})."),
            evidence={
                "ink": before,
                "fill": ground,
                "ratio": _floor(ratio, 2),
                "proposed_ink": after,
                "proposed_ratio": _floor(new_ratio, 2),
                "font_px": font["size_px"],
                "locator": region["locator"],
            },
            preview={"kind": "recolor", "from": seen, "to": better, "fill": fill[:3]},
        )


def local_findings(evidence):
    """Every local finding, the most blocking first: a covered main button, sideways scroll, then contrast."""
    ranked = []
    for frame in evidence["frames"]:
        for finding in (_covered_control(frame), _overflow(frame)):
            if finding:
                ranked.append((_PRIORITY.index(finding["check"]), 0.0, len(ranked), finding))
        for ratio, finding in _low_contrast(frame):
            ranked.append((_PRIORITY.index("contrast"), ratio, len(ranked), finding))
    return [item[3] for item in sorted(ranked, key=lambda item: item[:3])]
