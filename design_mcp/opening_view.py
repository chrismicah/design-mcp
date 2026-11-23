"""Turn measured browser bounds into an opening-view revision target."""

from math import ceil
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


CssPosition = Annotated[float, Field(ge=-100_000, le=100_000, allow_inf_nan=False, strict=True)]
ViewportSize = Annotated[int, Field(ge=1, le=16_384, strict=True)]
ControlLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class ControlBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: ControlLabel
    left: CssPosition
    top: CssPosition
    right: CssPosition
    bottom: CssPosition

    @model_validator(mode="after")
    def non_empty_bounds(self):
        if self.right <= self.left or self.bottom <= self.top:
            raise ValueError("Required controls need a positive width and height.")
        return self


class OpeningView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: ViewportSize
    height: ViewportSize
    required_controls: list[ControlBounds] = Field(min_length=1, max_length=6)


def revise_opening_view(view: OpeningView) -> dict:
    clipped = []
    for control in view.required_controls:
        excess = {
            "left": max(0, ceil(-control.left)),
            "top": max(0, ceil(-control.top)),
            "right": max(0, ceil(control.right - view.width)),
            "bottom": max(0, ceil(control.bottom - view.height)),
        }
        if any(excess.values()):
            clipped.append({"label": control.label, "overflow_css_px": excess})

    viewport = f"{view.width} × {view.height}"
    if not clipped:
        return {"why": f"All required control bounds fit in the measured {viewport} opening view.",
                "changes": {}}

    return {
        "why": f"Required controls extend beyond the measured {viewport} opening view.",
        "changes": {
            "viewport_css_px": {"width": view.width, "height": view.height},
            "clipped_controls": clipped,
            "composition": (
                "Use the measured overflow to set the amount of space to recover. "
                "Remove repeated content and excess space before the required controls first. "
                "Reflow the composition while preserving reading order, focus and control size."
            ),
            "recheck": (
                f"At the top of a fresh {viewport} viewport, capture the same required controls. "
                "Check their bounds, visibility and keyboard interaction before claiming a pass."
            ),
        },
    }
