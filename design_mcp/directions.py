"""Network-free art direction and revision tools."""

import json
import re
from urllib.parse import urlencode

from .design_checks import inspect_design
from .direction_records import Surface, library
from .models.visual_analyzer import contrast_ratio


_CAPS = {"direct": 6000, "react": 3200, "check": 2400}
_HOMEPAGE_TERMS = ("homepage", "home page", "home-page")
_TERMS = {
    "pricing": ("pricing", "price plan", "subscription tiers", "compare plans", "tier", "month"),
    "dashboard": ("dashboard", "dispatcher", "analytics", "metrics", "admin panel", "table", "reporting",
                  "turnaround board", "operations board", "work queue", "dispatch board", "stage manager",
                  "room readiness"),
    "mobile": ("mobile", "ticket", "platform", "boarding pass", "commuter", "onboarding", "qr"),
    "portfolio": ("portfolio", "case study", "work index", "studio project", "landscape", "architecture"),
    "editorial": ("editorial", "magazine", "article", "journal", "recipe", "field report"),
    "landing": ("landing", "launch", "product page", "bag", "shop", "roaster", "retail", *_HOMEPAGE_TERMS),
}

_FORM_SEPARATORS = str.maketrans("-\u2010\u2011", "   ")
_FORM_NAME = r"(?:forms?|questionnaires?|surveys?|polls?|rsvp|intake|registration|sign ?(?:in|up)|waitlist)"
# These phrases name formats, tools or records that have already been collected.
_NON_ENTRY = re.compile(
    r"\b(?:long|short|free) forms?\b|\bform factors?\b|\bin the form of\b"
    r"|\bform a (?:circle|line|team|group)\b|\bform (?:and|follows) function\b"
    r"|\b(?:completed|submitted|incoming|pending) forms\b"
    r"|\b(?:pull|merge|api|http) requests?\b"
    rf"|\b(?:{_FORM_NAME}|requests?|applications?)(?= (?:builders?|submissions?|results?|queues?|logs?|"
    r"trackers?|counts?|rates?|metrics|analytics|volume|status|dashboards?)\b)"
)
_FORM_TASK = re.compile(
    # Component names and tasks with a known answer structure.
    rf"\b{_FORM_NAME}\b"
    r"|\b(?:one|single) (?:question|decision|field)\b"
    r"|\b(?:register|enroll|vote)\s+(?:for|in|to|on)\b"
    r"|\b(?:job|grant|permit|membership)\s+application\b"
    r"|\b(?:access|leave|repair|service)\s+request\b"
    # Distinguish applying for something from applying a filter, and making a
    # request from viewing a record. A verb can take a brief-specific object.
    r"|\bapply(?:ing)?(?=\s+(?:for|online|on|from)\b|\s+to\b(?!\s+(?:all|each|every)\b)|[.!?]|$)"
    r"|(?:^|\b(?:to|can|could)\s+)request\b"
    r"|\brequest(?:ing)?\s+(?:a|an|their|your|access|help|leave|time off|support)\b"
    r"|\b(?:submit|send|file|complete|fill out)\s+(?:[\w-]+\s+){0,3}(?:request|application|feedback)\b"
    r"|\b(?:collect|enter|provide)\s+(?:(?:their|your|my|a|an)\s+)?"
    r"(?:names?|email|address(?:es)?|contact details|feedback)\b"
)
_PARENT_TASKS = (
    "landing", "landing page", "product page", "launch", "dashboard", "work queue", "operations board", "dispatch board",
    "portfolio", "case study", "work index", "pricing", "compare plans", "editorial", "magazine",
    "article", "mobile ticket", "boarding pass", *_HOMEPAGE_TERMS,
)
_CLAUSE_BREAK = re.compile(
    r"\b(?:with|includes?|including|about|of|for|to|where|featuring|showing|that|alongside|plus)\b|[.,;:!?]"
)
_FIELD_COLLECTION = re.compile(r"\b(?:collect|ask for|enter|provide|record)\b")
_ENTRY_OUTCOME = re.compile(r"\b(?:confirmation|submission|invalid|validat\w*|submitted)\b")
_EDITORIAL_HOMEPAGE = re.compile(r"\beditorial (?:homepage|home[ -]page)\b")


def _length(value) -> int:
    return len(json.dumps(value, ensure_ascii=False))


def _bounded(name: str, value: dict) -> dict:
    if _length(value) > _CAPS[name]:
        raise ValueError(f"{name} response exceeds the published limit")
    return value


def _match(token: str, brief: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(token.casefold())}(?!\w)", brief) is not None


def _is_form_task(text: str) -> bool:
    text = _NON_ENTRY.sub(" ", text.translate(_FORM_SEPARATORS))
    entry = _FORM_TASK.search(text)
    if entry is None and _ENTRY_OUTCOME.search(text):
        entry = _FIELD_COLLECTION.search(text)
    if entry is None:
        return False
    # The parent can precede the entry ("portfolio with a contact form") or
    # finish its noun phrase ("signup landing page"). "Mobile" alone is a size.
    preceding_clauses = _CLAUSE_BREAK.split(text[:entry.end()])[:-1]
    parent = " ".join(preceding_clauses)
    tail = _CLAUSE_BREAK.split(text[entry.end():], maxsplit=1)[0].rstrip()
    return not any(_match(term, parent) or tail.endswith(" " + term) for term in _PARENT_TASKS)


def _infer_surface(text: str) -> str | None:
    if _is_form_task(text):
        return "form"
    scores = {name: sum(_match(term, text) for term in terms) for name, terms in _TERMS.items()}
    if any(_match(term, text) for term in _HOMEPAGE_TERMS):
        # A homepage can be mobile-friendly or editorial in tone.
        if scores["mobile"] == 1 and _match("mobile", text):
            scores["mobile"] = 0
        if scores["editorial"] == 1 and _match("editorial", text) and not _EDITORIAL_HOMEPAGE.search(text):
            scores["editorial"] = 0
    explicit = [name for name, score in scores.items() if score and _match(name, text)]
    if len(explicit) == 1:
        return explicit[0]
    return max(scores, key=scores.get) if any(scores.values()) else None


async def direct(brief: str, surface: Surface | None = None, avoid: list[str] | None = None) -> dict:
    """Choose one sourced art direction for a brief. Call first for new interface work.

    Describe the audience, primary task, content and known brand constraints in ordinary language.
    Supply surface only when known. Use avoid for directions already rejected in this project.
    """
    text = brief.strip().casefold()
    if not text or len(text) > 12000:
        return {"error": "Enter a brief of 1 to 12,000 characters."}
    matched = surface or _infer_surface(text)
    kind = matched or "landing"
    candidates = [row for row in library().values() if row.surface == kind and row.id not in (avoid or [])]
    if not candidates:
        return {"error": f"No reviewed direction remains for {kind}.", "surface": kind}
    tag_text = text.translate(_FORM_SEPARATORS) if kind == "form" else text
    choice = max(candidates, key=lambda row: sum(_match(term, tag_text) for term in row.tags))
    questions = []
    if matched is None and len(text.split()) <= 8:
        questions = [{"question": "What will people use this screen for?",
                      "options": ["Explore an offering", "Work with information", "Read a story"],
                      "default": "Explore an offering"}]
    font_query = [("family", f"{choice.type.display}:wght@{choice.type.weight}"),
                  ("family", choice.type.body), ("display", "swap")]
    font_stylesheet = "https://fonts.googleapis.com/css2?" + urlencode(font_query)
    palette = choice.palette
    accent_text = max((palette.ink, palette.paper), key=lambda color: contrast_ratio(color, palette.accent))
    output = {
        "direction": choice.model_dump(exclude={"tags"}),
        "font_stylesheet": font_stylesheet,
        "interaction": {"accent_foreground": accent_text, "easing": "ease-out",
                        "focus": "Use a two-tone focus ring (2 px paper with 2 px ink outside) on the primary control.",
                        "accent_role": "Use the accent as a focal fill under accent_foreground. Check contrast before using it as text.",
                        "keyboard": "Expose the primary control by keyboard and announce pending and completed states."},
        "assumptions": [f"Use {kind} as the surface.", "Use only the project facts and assets in the brief."],
        "questions": questions,
        "handoff": "Apply the composition to the actual content. Preserve the task and brand constraints. "
                   "Fill label slots only with facts supplied by the brief. Use the source as design evidence. "
                   "Omit support regions that would only repeat facts. Keep visual and document order aligned. "
                   "Load the named fonts. Test the action, reading order and legibility at 390 px.",
    }
    if kind == "form":
        output["interaction"].update(
            focus="Bind each persistent label to its input. Give each focused control a 2px paper ring with a 2px ink outer ring.",
            accent_role="Reserve accent fill for the primary button and checked controls.",
            keyboard="Use native controls in reading order. On invalid submission, preserve entries and focus the first "
                     "invalid input. Mark each invalid field aria-invalid and link its correction text with aria-describedby.",
        )
    if choice.id == "service-work-order":
        output["interaction"].update(
            keyboard="Announce the selection through the one visible status. Keep it next to the chooser on desktop "
                     "and immediately after the choices on phones.",
        )
        output["handoff"] += (
            " At 320 × 700, check the complete short choice group and its result line from the top "
            "after keyboard and pointer selection."
        )
    return _bounded("direct", output)


async def react(direction_id: str, reaction: str, comparison_id: str | None = None) -> dict:
    """Give a targeted design revision. Accept calmer, bolder, too generic, or more like A.

    For more like A, provide comparison_id if A names another returned direction.
    Apply the delta to the current design while retaining its primary task and content.
    """
    records = library()
    row = records.get(direction_id)
    if row is None:
        return {"error": "Unknown direction ID. Call direct for a reviewed direction."}
    normalized = " ".join(reaction.casefold().split()).strip(".!")
    keep = ["primary task", "project content", "brand constraints", "accessibility"]
    if normalized in {"calmer", "quieter", "more calm", "less loud"}:
        if row.surface == "form":
            delta = {"spacing": "Increase the gap before the primary button from 24px to 32px."}
            why = "A little more space separates answering from acting."
            keep.extend([row.layout.focus, "primary action and its current label"])
        else:
            delta = {"type_ratio": max(2.5, round(row.type.ratio - .45, 2)),
                     "accent_usage": "Restrict the accent to the main control and focal marker.",
                     "spacing": "Increase negative space around the focal block by 20%.",
                     "motion_ms": min(400, row.motion.duration_ms + 60)}
            if row.id == "service-work-order":
                delta["spacing"] = (
                    "At 360 px and below preserve the existing order and spacing of the choice area. "
                    "Quiet the title with a smaller type size or tighter padding. Put extra whitespace beside the work order on desktop."
                )
                keep.append("a short choice list and its single live result visible at 320 × 700 without overflow")
            why = "Strengthen the breathing room without losing the primary action."
            if row.id == "exception-first":
                delta["accent_usage"] = (
                    "Keep the urgent exception as the strongest accent and echo that accent on its status in the queue. "
                    "Quiet routine rows and secondary controls. Keep the exception status labeled in words."
                )
                why = "Reduce competing accents while keeping the urgent exception easy to find."
    elif normalized in {"bolder", "more bold", "make it pop"}:
        delta = {"type_ratio": min(5, round(row.type.ratio + .45, 2)),
                 "composition": "Increase the focal block's horizontal span by one desktop grid column.",
                 "motion_ms": max(200, row.motion.duration_ms - 40)}
        why = "Give the main idea a larger silhouette while retaining the reading order."
    elif normalized in {"too generic", "less generic", "more distinctive"}:
        delta = {"composition": f"Replace one broad, reusable section with this subject-specific focus: {row.layout.focus}",
                 "imagery": row.imagery.subject, "mobile_order": row.layout.mobile}
        why = "Make the composition express the project's real content."
    elif normalized.startswith("more like ") or normalized == "a":
        requested = comparison_id or normalized.removeprefix("more like ")
        if requested in ("a", "a."):
            return {"direction_id": row.id, "needs_comparison": True,
                    "guidance": "For a visible variant A, name the change in hierarchy you want to keep or supply its direction ID."}
        alternate = records.get(requested)
        if alternate is None or alternate.surface != row.surface:
            return {"error": "Choose a reviewed comparison ID for the same surface."}
        delta = {"composition": alternate.layout.skeleton, "focus": alternate.layout.focus,
                 "mobile_order": alternate.layout.mobile, "type_ratio": alternate.type.ratio}
        why = "Apply the chosen variant's hierarchy to the current project."
    else:
        return {"error": "Try calmer, bolder, too generic, or more like A."}
    return _bounded("react", {"direction_id": row.id, "changes": delta, "why": why, "keep": keep})


async def check(source_code: str) -> dict:
    """Flag recognizable typography, composition and copy tells in HTML, JSX or CSS source."""
    if len(source_code) > 250000:
        return {"error": "Provide at most 250,000 characters, or check one section at a time."}
    findings = inspect_design(source_code)
    preview = []
    result = {"finding_count": len(findings), "findings": preview,
              "scope": "Source checks. A zero count needs rendered verification.",
              "render_checks": ["layout and overflow", "type scale and loaded fonts", "imagery and contrast",
                                "full interaction and reduced motion"]}
    for finding in findings:
        preview.append(finding)
        if _length(result) > _CAPS["check"] - 32:
            preview.pop()
            break
    result["truncated"] = len(preview) < len(findings)
    return _bounded("check", result)
