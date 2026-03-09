"""
Design Quality Scorer — heuristic-based scoring of design patterns 0-10.

Scoring dimensions:
  1. Metadata completeness (layout_type, color_mode, industry, behavioral_description, etc.)
  2. UI element richness (more diverse elements = higher quality)
  3. Tag diversity
  4. Source quality (curated > dribbble > webui-7kbal)
  5. Accessibility info presence
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..schema import DesignPattern


# Weights for each scoring dimension (must sum to 10)
WEIGHT_METADATA = 3.0
WEIGHT_UI_RICHNESS = 2.0
WEIGHT_TAG_DIVERSITY = 1.0
WEIGHT_SOURCE = 2.5
WEIGHT_ACCESSIBILITY = 1.5

SOURCE_SCORES = {
    "curated": 1.0,
    "dribbble": 0.6,
    "webui-7kbal": 0.25,
}

# Metadata fields we check for completeness
METADATA_FIELDS = [
    "layout_type",
    "layout_notes",
    "color_mode",
    "industry",
    "behavioral_description",
    "semantic_tokens",
    "image_url",
    "primary_colors",
    "component_hints",
    "visual_style",
    "ux_patterns",
]


def score_pattern(pattern: "DesignPattern") -> float:
    """Score a single design pattern from 0.0 to 10.0."""
    meta = _score_metadata(pattern)
    ui = _score_ui_richness(pattern)
    tags = _score_tag_diversity(pattern)
    source = _score_source(pattern)
    access = _score_accessibility(pattern)

    raw = (
        meta * WEIGHT_METADATA
        + ui * WEIGHT_UI_RICHNESS
        + tags * WEIGHT_TAG_DIVERSITY
        + source * WEIGHT_SOURCE
        + access * WEIGHT_ACCESSIBILITY
    )
    return round(min(max(raw, 0.0), 10.0), 2)


def _score_metadata(pattern: "DesignPattern") -> float:
    """0-1: What fraction of optional metadata fields are populated."""
    filled = 0
    total = len(METADATA_FIELDS)
    for field in METADATA_FIELDS:
        val = getattr(pattern, field, None)
        if val is not None:
            # Lists/dicts count as filled only if non-empty
            if isinstance(val, (list, dict)):
                if len(val) > 0:
                    filled += 1
            else:
                filled += 1
    return filled / total


def _score_ui_richness(pattern: "DesignPattern") -> float:
    """0-1: Based on diversity of ui_elements and ux_patterns."""
    ui_count = len(set(pattern.ui_elements))
    ux_count = len(set(pattern.ux_patterns))
    # 8+ unique UI elements is excellent, 4+ UX patterns is excellent
    ui_score = min(ui_count / 8.0, 1.0)
    ux_score = min(ux_count / 4.0, 1.0)
    return (ui_score * 0.6 + ux_score * 0.4)


def _score_tag_diversity(pattern: "DesignPattern") -> float:
    """0-1: Based on number of unique tags."""
    unique_tags = len(set(pattern.tags))
    # 6+ unique tags is excellent
    return min(unique_tags / 6.0, 1.0)


def _score_source(pattern: "DesignPattern") -> float:
    """0-1: Higher for curated sources."""
    return SOURCE_SCORES.get(pattern.source, 0.3)


def _score_accessibility(pattern: "DesignPattern") -> float:
    """0-1: Whether accessibility notes are present and substantive."""
    notes = pattern.accessibility_notes
    if not notes:
        return 0.0
    # Longer, more detailed notes score higher
    if len(notes) > 100:
        return 1.0
    if len(notes) > 30:
        return 0.7
    return 0.4
