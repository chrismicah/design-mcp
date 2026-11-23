"""Bundled, optional image disclosure source."""
from typing import Literal

from .resources import data_file

DETAIL_RESOURCE_URI = "design://patterns/image-detail"


def image_detail_source() -> str:
    """Read the offline HTML, CSS, and JavaScript example from the installed package."""
    return data_file("detail-disclosure.html").read_text(encoding="utf-8")


def get_component_pattern(pattern: Literal["image-detail"]) -> dict[str, str]:
    """Get working HTML for opening an image detail without losing context.

    Use image-detail when inspecting a known detail with a verified crop. Replace
    the image and text slots, keep the focus and return behavior, and apply the
    current brief's typography and color.
    """
    return {"pattern": pattern, "media_type": "text/html", "html": image_detail_source()}
