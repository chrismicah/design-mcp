"""A separate, script-free before/after page built from normalized evidence and local findings.

The page is one self-contained file whose only image is the capture itself, embedded as data. Its
policy blocks scripts, network requests, inline style attributes and form submission, and pins the
style sheet by hash. The after view recolors the captured pixels of one region with an SVG filter, so
no page markup, fonts or third-party assets are copied and the live site is never touched.
"""

import base64
import hashlib
import html
import re
from urllib.parse import urlsplit

from .checks import contrast_ratio, hex_color
from .evidence import UNKNOWN

PALETTE = {"ink": "#16181d", "muted": "#565b66", "paper": "#f6f5f1", "line": "#cfccc2", "mark": "#b4235a"}

_CSS = ":root{" + ";".join(f"--{name}:{value}" for name, value in PALETTE.items()) + "}" + """
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 "Avenir Next","Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1240px;margin:0 auto;padding:28px 24px 72px}
.where{margin:0 0 10px;color:var(--muted);font-size:14px}
h1{margin:0;max-width:44em;font-size:24px;line-height:1.3;font-weight:600}
.fix{margin:16px 0 0;max-width:46em}
.fix div{display:grid;grid-template-columns:5.5em 1fr;gap:12px;padding:8px 0;border-top:1px solid var(--line)}
.fix dt{padding-top:2px;color:var(--muted);font-size:14px}
.fix dd{margin:0}
.compare{display:flex;align-items:center;margin:26px 0 8px}
.compare input{position:absolute;opacity:0;width:1px;height:1px}
.compare label{min-width:104px;padding:9px 20px;border:1.5px solid var(--ink);font-weight:600;text-align:center;cursor:pointer}
.compare label:first-of-type{border-radius:6px 0 0 6px}
.compare label:last-of-type{border-left:0;border-radius:0 6px 6px 0}
.compare input:checked+label{background:var(--ink);color:var(--paper)}
.compare input:focus-visible+label{outline:3px solid var(--mark);outline-offset:3px}
.state{margin:0 0 12px;max-width:46em}
.state-after,.after{display:none}
body:has(#view-after:checked) .state-before{display:none}
body:has(#view-after:checked) .state-after{display:block}
body:has(#view-after:checked) .after{display:inline}
.stage{display:inline-block;max-width:100%;margin:0;border:1px solid var(--line);background:#fff;line-height:0}
.shot{display:block;max-width:100%;height:auto}
.halo{fill:none;stroke:#fff;stroke-width:6;vector-effect:non-scaling-stroke}
.mark{fill:none;stroke:var(--mark);stroke-width:2.5;vector-effect:non-scaling-stroke}
figcaption{padding:10px 14px;border-top:1px solid var(--line);color:var(--muted);font-size:14px;line-height:1.5}
h2{margin:44px 0 10px;font-size:17px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:8px 12px 8px 0;border-top:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:500}
tr.hit td{font-weight:600}
.chip{margin-right:4px;vertical-align:-2px}
.notes{margin:28px 0 0;padding:0;list-style:none;color:var(--muted);font-size:14px}
.notes li{padding:3px 0}
@media (max-width:640px){main{padding:20px 16px 56px}h1{font-size:21px}.fix div{grid-template-columns:1fr;gap:2px}}
"""

_STYLE_HASH = base64.b64encode(hashlib.sha256(_CSS.encode("utf-8")).digest()).decode("ascii")
CSP = f"default-src 'none'; img-src data:; style-src 'sha256-{_STYLE_HASH}'; base-uri 'none'; form-action 'none'"

_BASE64 = re.compile(r"[A-Za-z0-9+/]+={0,2}")
_SOURCE = {
    "active-tab": "from the tab you scanned",
    "pasted-url": "from the page you opened",
    "isolated-url": "in a separate, cookie-free browser",
}


def _e(value):
    return html.escape(str(value), quote=True)


def _n(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _percent(value):
    return f"{round(value * 100)}%"


def recolor_matrix(old_ink, new_ink, fill):
    """Rows for an SVG feColorMatrix that moves text from `old_ink` to `new_ink` on a flat `fill`.

    Antialiased text pixels are blends of ink and fill. The channel where ink and fill differ most gives
    the blend amount, and every output channel is rebuilt from it, so the fill stays exactly as captured
    and the glyph shapes are the page's own. Returns None when ink and fill are the same color.
    """
    key = max(range(3), key=lambda index: abs(old_ink[index] - fill[index]))
    span = old_ink[key] - fill[key]
    if span == 0:
        return None
    rows = []
    for channel in range(3):
        gain = (new_ink[channel] - fill[channel]) / span
        row = [0.0, 0.0, 0.0, 0.0, (fill[channel] - gain * fill[key]) / 255]
        row[key] = gain
        rows.append(row)
    rows.append([0.0, 0.0, 0.0, 1.0, 0.0])
    return rows


def after_matrix(critique):
    """The recolor matrix behind a finding's after view, or None when the finding has no after view."""
    plan = critique["preview"] if critique else None
    if not plan or plan["kind"] != "recolor" or not critique["box"]:
        return None
    return recolor_matrix(plan["from"], plan["to"], plan["fill"])


def _chip(rgb):
    return ('<svg class="chip" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true">'
            f'<rect width="12" height="12" fill="{hex_color(rgb)}" stroke="{PALETTE["ink"]}"/></svg>')


def _region_row(region, hit):
    name = _e(region["name"])
    if region["masked"]:
        name += " (field, blanked out)"
    inside = [region["landmark"]] if region["landmark"] != UNKNOWN else []
    if region["heading"] != UNKNOWN:
        inside.append(f"under “{region['heading']}”")
    font = region["font"]
    size = f"{_n(font['size_px'])} px" if font["size_px"] != UNKNOWN else "size unknown"
    weight = f"weight {font['weight']}" if font["weight"] != UNKNOWN else "weight unknown"
    family = font["family"] if font["family"] != UNKNOWN else "family unknown"
    ink, fill = region["ink"], region["fill"]
    if UNKNOWN in (ink, fill):
        colors = "unknown"
    else:
        colors = f"{_chip(ink)}{hex_color(ink)} on {_chip(fill)}{hex_color(fill)}"
        if region["fill_flat"] is True and ink[3] == 1 and fill[3] == 1:
            colors += f" · {contrast_ratio(ink, fill):.2f} to 1"
    box = region["box"]
    position = (f"left {_percent(box['x'])}, top {_percent(box['y'])}, "
                f"{_percent(box['width'])} × {_percent(box['height'])} of the view")
    order = region["reading_order"] if region["reading_order"] != UNKNOWN else "?"
    row = '<tr class="hit">' if hit else "<tr>"
    return (f'{row}<td>{order}</td>'
            f'<td>{name}<br>{_e(region["role"])}</td><td>{_e(" · ".join(inside) or "unknown")}</td>'
            f'<td>{_e(family)}<br>{size}, {weight}</td><td>{colors}</td><td>{position}</td></tr>')


def build_preview(evidence, findings):
    """Return one self-contained HTML document for the first finding (or for a clean result)."""
    critique = findings[0] if findings else None
    frames, capture = evidence["frames"], evidence["capture"]
    frame = next((item for item in frames if critique and item["id"] == critique["frame"]), frames[0])
    width, height = frame["viewport"]["width"], frame["viewport"]["height"]
    shot = frame["screenshot"]["data"]
    if not _BASE64.fullmatch(shot):
        raise ValueError("build_preview needs normalized evidence")
    address = urlsplit(capture["url"])
    place = (address.netloc + address.path)[:72]
    title = capture["title"] if capture["title"] != UNKNOWN else address.netloc

    box = critique["box"] if critique else None
    plan = critique["preview"] if critique else None
    matrix = after_matrix(critique)
    mark = filter_def = after_layer = ""
    if box:
        x, y, w, h = box["x"] * width, box["y"] * height, box["width"] * width, box["height"] * height
        left, top = max(1.0, x - 4), max(1.0, y - 4)
        right, bottom = min(width - 1.0, x + w + 4), min(height - 1.0, y + h + 4)
        outline = f'x="{_n(left)}" y="{_n(top)}" width="{_n(right - left)}" height="{_n(bottom - top)}"'
        mark = f'<rect class="halo" {outline}/><rect class="mark" {outline}/>'
        if matrix:
            values = " ".join(f"{value:.5f}" for row in matrix for value in row)
            filter_def = (f'<filter id="recolor" filterUnits="userSpaceOnUse" x="{_n(x)}" y="{_n(y)}" '
                          f'width="{_n(w)}" height="{_n(h)}" color-interpolation-filters="sRGB">'
                          f'<feColorMatrix type="matrix" values="{values}"/></filter>')
            after_layer = '<use class="after" href="#shot" filter="url(#recolor)"/>'

    if critique:
        count = len(findings)
        position = "1 local finding" if count == 1 else f"finding 1 of {count}"
        heading = _e(critique["problem"])
        fix = (f'<dl class="fix"><div><dt>Change</dt><dd>{_e(critique["change"])}</dd></div>'
               f'<div><dt>Check</dt><dd>{_e(critique["outcome"])}</dd></div></dl>')
    else:
        position = "no local findings"
        heading = "Local checks found nothing to fix in this view."
        fix = ('<p class="fix">Checked for sideways scroll, a covered main button, and low-contrast text '
               'on flat backgrounds.</p>')

    outlined = " The outlined area is where the change applies." if mark else ""
    if after_layer:
        compare = (
            '<div class="compare" role="radiogroup" aria-label="Before or after the change">'
            '<input type="radio" name="view" id="view-before" checked><label for="view-before">Before</label>'
            '<input type="radio" name="view" id="view-after"><label for="view-after">After</label></div>\n'
            f'<p class="state state-before">Showing the page as captured.{outlined}</p>\n'
            f'<p class="state state-after">Showing the proposed change: text color {hex_color(plan["to"])} in place '
            f'of {hex_color(plan["from"])}. Everything else is the captured page.</p>\n'
        )
    elif critique and plan:
        compare = ('<p class="state">No after view: the text and its background are the same color in the '
                   f"capture, so there are no text pixels to recolor.{outlined}</p>\n")
    elif critique:
        compare = ('<p class="state">No after view for this change: it moves layout, and this build only previews '
                   f"color changes made from the captured pixels.{outlined}</p>\n")
    else:
        compare = ""

    label = f"Capture of {title} at {width} px wide." + (" The outlined area is the subject of the finding." if mark else "")
    when = f" · captured {capture['captured_at']}" if capture["captured_at"] != UNKNOWN else ""
    source = f" · {_SOURCE[capture['source']]}" if capture["source"] in _SOURCE else ""
    rows = "".join(_region_row(region, bool(critique) and region["id"] == critique["region"])
                   for region in frame["regions"])

    counts = frame["masks"]["counts"]
    blanked = [f"{counts[kind]} {words}" for kind, words in
               (("field", "form fields"), ("editable", "editable areas"), ("frame", "embedded frames")) if counts[kind]]
    notes = []
    if blanked:
        notes.append("Blanked out before the capture was saved: " + ", ".join(blanked) + ".")
    if len(frames) > 1:
        sizes = ", ".join(f"{item['viewport']['width']} px" for item in frames)
        notes.append(f"Views captured: {sizes} wide. This page shows the {width} px view.")
    notes.append(f"Page address stored as {capture['url']}. Sign-in details, tokens and anything after # are removed.")
    notes.append("Visual review by a model: not run. Nothing was uploaded.")
    notes.append("This file has no scripts and loads nothing from the network.")
    notes.extend(evidence["notes"])

    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="referrer" content="no-referrer">\n'
        f"<title>Review of {_e(title)}</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n<main>\n"
        f'<p class="where">{_e(place)} · {width} px wide · {position}</p>\n'
        f"<h1>{heading}</h1>\n{fix}\n{compare}"
        '<figure class="stage">\n'
        f'<svg class="shot" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{_e(label)}">'
        f'<defs><image id="shot" width="{width}" height="{height}" preserveAspectRatio="none" '
        f'href="data:image/png;base64,{shot}"/>{filter_def}</defs>'
        f'<use href="#shot"/>{after_layer}{mark}</svg>\n'
        f"<figcaption>{width} × {height} px view{_e(when)}{_e(source)}</figcaption>\n</figure>\n"
        "<h2>What was measured in this view</h2>\n"
        '<table><thead><tr><th scope="col">Order</th><th scope="col">Region</th><th scope="col">Inside</th>'
        '<th scope="col">Type</th><th scope="col">Text on background</th><th scope="col">Position</th></tr></thead>'
        f"<tbody>{rows}</tbody></table>\n"
        '<ul class="notes">' + "".join(f"<li>{_e(note)}</li>" for note in notes) + "</ul>\n"
        "</main>\n</body>\n</html>\n"
    )
