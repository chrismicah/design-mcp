import json

from pydantic import ValidationError
import pytest

from design_mcp.directions import react
from design_mcp.opening_view import ControlBounds, OpeningView


def opening(width=320, height=700, **control):
    return OpeningView(width=width, height=height, required_controls=[ControlBounds(**control)])


@pytest.mark.asyncio
async def test_react_returns_exact_round_up_at_the_failed_viewport():
    view = opening(label="Preview reminder", left=16, top=818.875, right=185.5, bottom=867.65625)
    result = await react("direct-consultation", "Fit the opening view.", opening_view=view)
    assert result["direction_id"] == "direct-consultation"
    assert result["changes"]["viewport_css_px"] == {"width": 320, "height": 700}
    assert result["changes"]["clipped_controls"] == [{
        "label": "Preview reminder", "overflow_css_px": {"left": 0, "top": 0, "right": 0, "bottom": 168},
    }]
    assert "Remove repeated content" in result["changes"]["composition"]


@pytest.mark.asyncio
async def test_react_keeps_passing_view_and_requests_measurements_when_missing():
    view = opening(390, 844, label="Preview reminder", left=16, top=773.84375, right=186, bottom=822.625)
    assert (await react("direct-consultation", "fit the opening view", opening_view=view))["changes"] == {}
    assert "Capture" in (await react("direct-consultation", "fit the opening view"))["error"]


@pytest.mark.asyncio
async def test_react_reports_each_clipped_side_and_respects_response_limit():
    view = OpeningView(width=320, height=700, required_controls=[
        ControlBounds(label=f"Required control {n} " + "界" * 50, left=-5.2, top=-1.1, right=321, bottom=800)
        for n in range(6)
    ])
    result = await react("direct-consultation", "fit the opening view", opening_view=view)
    clipped = result["changes"]["clipped_controls"]
    assert len(clipped) == 6
    assert clipped[0]["overflow_css_px"] == {"left": 6, "top": 2, "right": 1, "bottom": 100}
    assert len(json.dumps(result, ensure_ascii=False).encode()) <= 3200


@pytest.mark.parametrize("overrides", [
    {"left": 60, "right": 40},
    {"bottom": float("inf")},
    {"top": float("nan")},
    {"label": " "},
])
def test_rejects_unusable_control_measurements(overrides):
    bounds = {"label": "Call", "left": 12, "top": 40, "right": 260, "bottom": 80, **overrides}
    with pytest.raises(ValidationError):
        opening(**bounds)
