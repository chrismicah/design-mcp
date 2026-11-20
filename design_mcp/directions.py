"""Network-free art direction and revision tools."""

import json
import re

from .design_checks import inspect_design
from .direction_records import Surface, library
from .models.visual_analyzer import contrast_ratio


_CAPS = {"direct": 6000, "react": 3200, "check": 2400}
_TERMS = {
    "pricing": ("pricing", "price plan", "subscription tiers", "compare plans", "tier", "month"),
    "dashboard": ("dashboard", "dispatcher", "analytics", "metrics", "admin panel", "table", "reporting"),
    "mobile": ("mobile", "ticket", "platform", "boarding pass", "commuter", "onboarding", "qr"),
    "portfolio": ("portfolio", "case study", "work index", "studio project", "landscape", "architecture"),
    "editorial": ("editorial", "magazine", "article", "journal", "recipe", "field report"),
    "landing": ("landing", "launch", "product page", "bag", "shop", "roaster", "retail"),
}


def _length(value) -> int:
    return len(json.dumps(value, ensure_ascii=False))


def _bounded(name: str, value: dict) -> dict:
    if _length(value) > _CAPS[name]:
        raise ValueError(f"{name} response exceeds the published limit")
    return value


def _match(token: str, brief: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(token.casefold())}(?!\w)", brief) is not None


async def direct(brief: str, surface: Surface | None = None, avoid: list[str] | None = None) -> dict:
    """Choose one sourced art direction for a brief. Call first for new interface work.

    Describe the audience, primary task, content and known brand constraints in ordinary language.
    Supply surface only when known. Use avoid for directions already rejected in this project.
    """
    text = brief.strip().casefold()
    if not text or len(text) > 12000:
        return {"error": "Enter a brief of 1 to 12,000 characters."}
    genre_scores = {name: sum(_match(term, text) for term in terms) for name, terms in _TERMS.items()}
    explicit = [name for name in _TERMS if _match(name, text)]
    if len(explicit) == 1:
        inferred = explicit[0]
    else:
        inferred = max(genre_scores, key=genre_scores.get) if max(genre_scores.values()) else "landing"
    kind = surface or inferred
    candidates = [row for row in library().values() if row.surface == kind and row.id not in (avoid or [])]
    if not candidates:
        return {"error": f"No reviewed direction remains for {kind}.", "surface": kind}
    choice = max(candidates, key=lambda row: sum(_match(term, text) for term in row.tags))
    questions = []
    if surface is None and not any(genre_scores.values()) and len(text.split()) <= 8:
        questions = [{"question": "What will people use this screen for?",
                      "options": ["Explore an offering", "Work with information", "Read a story"],
                      "default": "Explore an offering"}]
    palette = choice.palette
    accent_text = max((palette.ink, palette.paper), key=lambda color: contrast_ratio(color, palette.accent))
    output = {
        "direction": choice.model_dump(exclude={"tags"}),
        "interaction": {"accent_foreground": accent_text, "easing": "ease-out",
                        "focus": "Use a two-tone focus ring (2 px paper with 2 px ink outside) on the primary control.",
                        "accent_role": "Use the accent as a focal fill under accent_foreground. Check contrast before using it as text.",
                        "keyboard": "Expose the primary control by keyboard and announce pending and completed states."},
        "assumptions": [f"Use {kind} as the surface.", "Use only the project facts and assets in the brief."],
        "questions": questions,
        "handoff": "Apply the composition to the actual content. Preserve the task and brand constraints. "
                   "Fill label slots only with facts supplied by the brief. Use the source as design evidence. "
                   "Verify the action, reading order and legibility at 390 px.",
    }
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
    if normalized in {"calmer", "quieter", "more calm", "less loud"}:
        delta = {"type_ratio": max(2.5, round(row.type.ratio - .45, 2)),
                 "accent_usage": "Restrict the accent to the main control and focal marker.",
                 "spacing": "Increase negative space around the focal block by 20%.",
                 "motion_ms": min(400, row.motion.duration_ms + 60)}
        why = "Strengthen the breathing room without losing the primary action."
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
    return _bounded("react", {"direction_id": row.id, "changes": delta, "why": why,
                              "keep": ["primary task", "project content", "brand constraints", "accessibility"]})


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
