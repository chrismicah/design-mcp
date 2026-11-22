"""Compact, versioned page evidence.

A capture from the extension or an isolated renderer is untrusted input. `normalize` returns a new
bundle built only from allowlisted fields: web addresses are scrubbed, text is shortened, numbers are
bounded and anything missing is marked `unknown`. Only this module's output is stored or rendered.
"""

import base64
import binascii
import hashlib
import math
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

SCHEMA = "design-mcp.page-evidence/1"
UNKNOWN = "unknown"
MAX_FRAMES = 4
MAX_REGIONS = 8
MAX_SCREENSHOT_BYTES = 12 * 1024 * 1024
MAX_NAME = 80

_INCOMPLETE = "The capture was incomplete, so nothing was saved. Scan the page again."
_SOURCES = ("active-tab", "pasted-url", "isolated-url")
_STATES = ("initial", "after-activation")
_PRESSED = ("true", "false", "mixed")
_MASK_KINDS = ("field", "editable", "frame")
_DEFAULT_PORT = {"http": 80, "https": 443}
_REGION_ID = re.compile(r"r[0-9]{1,3}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\Z")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Chunks that affect how pixels look. Text, time and EXIF chunks are dropped.
_PNG_KEEP = (b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"iCCP", b"sBIT", b"pHYs")

_CONTROL = re.compile("[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202e\u2066-\u2069]")
_LOCAL_URL = re.compile(r"(?i)\b(?:data:[\w.+-]*/\S*|data:,\S*|file:/\S*|blob:\S+|javascript:\S+|vbscript:\S+)")
_WEB_URL_TAIL = re.compile(r"(?i)(https?://[^\s?#]+)[?#]\S*")
_CREDENTIAL_WORDS = frozenset(
    "auth authorization bearer code credential credentials jwt key apikey otp pass passwd password pwd secret "
    "session sessionid phpsessid jsessionid sid sig signature sso state ticket token accesstoken idtoken "
    "refreshtoken".split()
)
_TOKEN_LIKE = re.compile(r"^[A-Za-z0-9_\-+/=.~%]{24,}$")


class EvidenceError(ValueError):
    """A capture that cannot be accepted. `code` is stable; `message` is written for the person scanning."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def clean_text(value, limit=MAX_NAME):
    """Short display text without control characters, local URLs or URL queries. Missing becomes `unknown`."""
    if not isinstance(value, str):
        return UNKNOWN
    text = _CONTROL.sub(" ", value)
    text = _LOCAL_URL.sub("[removed]", text)
    text = _WEB_URL_TAIL.sub(r"\1", text)
    text = " ".join(text.split())
    if not text:
        return UNKNOWN
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _credential_pair(key, value):
    words = re.findall(r"[a-z]+", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key).lower())
    if any(word in _CREDENTIAL_WORDS for word in words) or "".join(words) in _CREDENTIAL_WORDS:
        return True
    return bool(_TOKEN_LIKE.match(value)) and any(c.isdigit() for c in value) and any(c.isalpha() for c in value)


def inspect_url(url):
    """Return `(clean_url, removed)` for an http(s) page address.

    The clean address has no sign-in details, no credential-like query values and no fragment.
    `removed` describes any credentials that were taken out, in words a person can act on.
    """
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        raise EvidenceError("unsupported-url", "This page has no web address that can be reviewed.")
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        raise EvidenceError("unsupported-url", "That web address is not valid.") from None
    if parts.scheme not in _DEFAULT_PORT or not parts.hostname:
        raise EvidenceError("unsupported-url", "Only http and https pages can be reviewed.")
    removed = []
    if parts.username is not None or parts.password is not None:
        removed.append("a sign-in name or password")
    kept = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if _credential_pair(key, value):
            removed.append(f"the value of “{clean_text(key, 40)}”")
        else:
            kept.append((key, value))
    host = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
    netloc = host if port in (None, _DEFAULT_PORT[parts.scheme]) else f"{host}:{port}"
    return urlunsplit((parts.scheme, netloc, parts.path or "/", urlencode(kept), "")), removed


def scrub_url(url):
    """The address as it may be stored: see `inspect_url`."""
    return inspect_url(url)[0]


def _num(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return value if low <= value <= high else None


def _rgba(value):
    if not isinstance(value, (list, tuple)) or len(value) not in (3, 4):
        return UNKNOWN
    channels = [_num(channel, 0, 255) for channel in value[:3]]
    alpha = _num(value[3], 0, 1) if len(value) == 4 else 1
    if None in channels or alpha is None:
        return UNKNOWN
    return [round(channel) for channel in channels] + [round(alpha, 3)]


def _box(value):
    """A viewport-normalized box clipped to the viewport, or None when none of it is visible."""
    if not isinstance(value, dict):
        return None
    x, y, width, height = (_num(value.get(key), -50, 50) for key in ("x", "y", "width", "height"))
    if None in (x, y, width, height) or width <= 0 or height <= 0:
        return None
    left, top, right, bottom = max(0.0, x), max(0.0, y), min(1.0, x + width), min(1.0, y + height)
    if right <= left or bottom <= top:
        return None
    return {
        "x": round(left, 4),
        "y": round(top, 4),
        "width": round(right - left, 4),
        "height": round(bottom - top, 4),
    }


def _region(raw):
    if not isinstance(raw, dict):
        return None
    box = _box(raw.get("box"))
    if box is None:
        return None
    font = raw.get("font") if isinstance(raw.get("font"), dict) else {}
    size = _num(font.get("size_px"), 1, 512)
    weight = _num(font.get("weight"), 1, 1000)
    order = _num(raw.get("reading_order"), 0, 100000)
    pressed = raw.get("pressed")
    fill_flat = raw.get("fill_flat")
    return {
        "id": UNKNOWN,
        "role": clean_text(raw.get("role"), 24),
        "name": clean_text(raw.get("name")),
        "landmark": clean_text(raw.get("landmark"), 24),
        "heading": clean_text(raw.get("heading")),
        "locator": clean_text(raw.get("locator"), 160),
        "reading_order": int(order) if order is not None else UNKNOWN,
        "box": box,
        "font": {
            "family": clean_text(font.get("family"), 60),
            "size_px": size if size is not None else UNKNOWN,
            "weight": int(weight) if weight is not None else UNKNOWN,
        },
        "ink": _rgba(raw.get("ink")),
        "fill": _rgba(raw.get("fill")),
        "fill_flat": fill_flat if isinstance(fill_flat, bool) else UNKNOWN,
        "has_text": raw.get("has_text") is True,
        "masked": raw.get("masked") is True,
        "disabled": raw.get("disabled") is True,
        "pressed": pressed if isinstance(pressed, str) and pressed in _PRESSED else UNKNOWN,
    }


def _screenshot(raw):
    if not isinstance(raw, dict) or raw.get("media_type") != "image/png" or not isinstance(raw.get("data"), str):
        raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.")
    if len(raw["data"]) > MAX_SCREENSHOT_BYTES * 4 // 3 + 8:
        raise EvidenceError("too-large", "The screenshot is larger than this version accepts.")
    try:
        source = base64.b64decode(raw["data"], validate=True)
    except (binascii.Error, ValueError):
        raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.") from None
    if not source.startswith(_PNG_SIGNATURE) or source[12:16] != b"IHDR" or len(source) < 45:
        raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.")
    width, height = int.from_bytes(source[16:20], "big"), int.from_bytes(source[20:24], "big")
    if not (1 <= width <= 16384 and 1 <= height <= 16384):
        raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.")
    kept, position, ended = [_PNG_SIGNATURE], len(_PNG_SIGNATURE), False
    while position + 12 <= len(source) and not ended:
        length = int.from_bytes(source[position:position + 4], "big")
        kind = source[position + 4:position + 8]
        end = position + 12 + length
        if end > len(source):
            raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.")
        if kind in _PNG_KEEP:
            kept.append(source[position:end])
        ended = kind == b"IEND"
        position = end
    if not ended:
        raise EvidenceError("malformed", "The capture has no usable screenshot. Scan the page again.")
    pixels = b"".join(kept)
    return {
        "media_type": "image/png",
        "data": base64.b64encode(pixels).decode("ascii"),
        "width": width,
        "height": height,
        "sha256": hashlib.sha256(pixels).hexdigest(),
    }


def _frame(raw, index, notes):
    if not isinstance(raw, dict):
        raise EvidenceError("malformed", _INCOMPLETE)
    frame_id = f"f{index + 1}"
    viewport = raw.get("viewport") if isinstance(raw.get("viewport"), dict) else {}
    width, height = _num(viewport.get("width"), 200, 8192), _num(viewport.get("height"), 200, 8192)
    if width is None or height is None:
        raise EvidenceError("malformed", _INCOMPLETE)
    dpr = _num(viewport.get("dpr"), 0.25, 8)
    document = raw.get("document") if isinstance(raw.get("document"), dict) else {}
    scroll_width = _num(document.get("scroll_width"), 0, 200000)
    client_width = _num(document.get("client_width"), 0, 200000)

    regions, ids, dropped = [], set(), 0
    for item in raw.get("regions") if isinstance(raw.get("regions"), list) else []:
        region = _region(item)
        if region is None:
            continue
        if len(regions) == MAX_REGIONS:
            dropped += 1
            continue
        wanted = item.get("id")
        if not (isinstance(wanted, str) and _REGION_ID.match(wanted)) or wanted in ids:
            wanted = next(f"r{n}" for n in range(1, 1000) if f"r{n}" not in ids)
        region["id"] = wanted
        ids.add(wanted)
        regions.append(region)
    if dropped:
        notes.append(f"{frame_id}: {dropped} regions beyond the limit of {MAX_REGIONS} were left out.")

    overflow = None
    raw_overflow = raw.get("overflow")
    if isinstance(raw_overflow, dict):
        overflow = {
            "name": clean_text(raw_overflow.get("name")),
            "locator": clean_text(raw_overflow.get("locator"), 160),
            "box": _box(raw_overflow.get("box")),
        }

    primary = None
    raw_primary = raw.get("primary_control")
    if isinstance(raw_primary, dict) and isinstance(raw_primary.get("region"), str) and raw_primary["region"] in ids:
        covered_by = None
        cover = raw_primary.get("covered_by")
        if isinstance(cover, dict) and isinstance(cover.get("position"), str) and cover["position"] in ("fixed", "sticky"):
            cover_height = _num(cover.get("height_px"), 0, 8192)
            covered_by = {
                "position": cover["position"],
                "name": clean_text(cover.get("name")),
                "locator": clean_text(cover.get("locator"), 160),
                "box": _box(cover.get("box")),
                "height_px": round(cover_height) if cover_height is not None else UNKNOWN,
            }
        primary = {
            "region": raw_primary["region"],
            "basis": clean_text(raw_primary.get("basis"), 80),
            "covered_by": covered_by,
        }

    raw_masks = raw.get("masks") if isinstance(raw.get("masks"), dict) else {}
    counts = dict.fromkeys(_MASK_KINDS, 0)
    for item in raw_masks.get("boxes") if isinstance(raw_masks.get("boxes"), list) else []:
        if isinstance(item, dict) and isinstance(item.get("kind"), str) and item["kind"] in counts:
            counts[item["kind"]] += 1
    private = any(counts.values()) or any(region["masked"] for region in regions)
    if private and raw_masks.get("applied") is not True:
        raise EvidenceError(
            "private-data",
            "This page has form fields or embedded frames that were not blanked out, so nothing was saved. "
            "Scan the page again.",
        )

    state = raw.get("state")
    return {
        "id": frame_id,
        "state": state if isinstance(state, str) and state in _STATES else "initial",
        "viewport": {
            "width": int(width),
            "height": int(height),
            "dpr": round(dpr, 2) if dpr is not None else UNKNOWN,
        },
        "document": {
            "scroll_width": int(scroll_width) if scroll_width is not None else UNKNOWN,
            "client_width": int(client_width) if client_width is not None else UNKNOWN,
            "lang": clean_text(document.get("lang"), 16),
        },
        "screenshot": _screenshot(raw.get("screenshot")),
        "regions": regions,
        "overflow": overflow,
        "primary_control": primary,
        "masks": {"applied": True, "counts": counts},
    }


def _interaction(raw):
    """One authorized keyboard activation and what it changed. Anything not authorized is not kept."""
    if not isinstance(raw, dict) or raw.get("authorized") is not True:
        return None
    delta = raw.get("delta") if isinstance(raw.get("delta"), dict) else {}

    def pair(key, clean):
        value = delta.get(key)
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return [clean(value[0]), clean(value[1])]
        return UNKNOWN

    def rows(value):
        return int(value) if _num(value, 0, 100000) is not None else UNKNOWN

    key = raw.get("key")
    bounds_changed = delta.get("bounds_changed")
    return {
        "kind": "keyboard-activation",
        "authorized": True,
        "key": key if isinstance(key, str) and key in ("Enter", "Space") else UNKNOWN,
        "target": clean_text(raw.get("target"), 16),
        "delta": {
            "focus": pair("focus", clean_text),
            "pressed": pair("pressed", lambda value: value if isinstance(value, str) and value in _PRESSED else UNKNOWN),
            "visible_rows": pair("visible_rows", rows),
            "bounds_changed": bounds_changed if isinstance(bounds_changed, bool) else UNKNOWN,
        },
    }


def _timings(raw):
    raw = raw if isinstance(raw, dict) else {}
    timings = {}
    for key in ("page_load", "capture"):
        value = _num(raw.get(key), 0, 600000)
        timings[key] = round(value) if value is not None else UNKNOWN
    return timings


def normalize(bundle):
    """Validate and scrub one capture. Returns a new dict or raises `EvidenceError`."""
    if not isinstance(bundle, dict) or bundle.get("schema") != SCHEMA:
        raise EvidenceError("unsupported-schema", "This capture is not in a format this version understands.")
    raw_capture = bundle.get("capture") if isinstance(bundle.get("capture"), dict) else {}
    if raw_capture.get("user_triggered") is not True:
        raise EvidenceError("not-user-triggered", "A scan only runs when you start it. Nothing was saved.")
    url = scrub_url(raw_capture.get("url"))
    raw_frames = bundle.get("frames")
    if not isinstance(raw_frames, list) or not raw_frames:
        raise EvidenceError("malformed", _INCOMPLETE)
    if len(raw_frames) > MAX_FRAMES:
        raise EvidenceError("too-large", "The capture has more views than this version accepts.")
    notes = []
    frames = [_frame(raw, index, notes) for index, raw in enumerate(raw_frames)]
    source = raw_capture.get("source")
    captured_at = raw_capture.get("captured_at")
    identity = hashlib.sha256((url + "\n" + frames[0]["screenshot"]["sha256"]).encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA,
        "capture": {
            "id": "c-" + identity[:12],
            "source": source if isinstance(source, str) and source in _SOURCES else UNKNOWN,
            "url": url,
            "title": clean_text(raw_capture.get("title"), 120),
            "captured_at": captured_at if isinstance(captured_at, str) and _TIMESTAMP.match(captured_at) else UNKNOWN,
            "user_triggered": True,
        },
        "frames": frames,
        "interaction": _interaction(bundle.get("interaction")),
        "timings_ms": _timings(bundle.get("timings_ms")),
        "notes": notes,
    }
