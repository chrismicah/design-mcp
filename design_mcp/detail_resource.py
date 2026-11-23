"""Bundled, optional image disclosure source."""
from .resources import data_file

DETAIL_RESOURCE_URI = "design://patterns/image-detail"


def image_detail_source() -> str:
    """Read the offline HTML, CSS, and JavaScript example from the installed package."""
    return data_file("detail-disclosure.html").read_text(encoding="utf-8")
