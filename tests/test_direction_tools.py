import json
from pathlib import Path

import pytest

from design_mcp.directions import check, direct, react
from design_mcp.direction_records import library


@pytest.mark.asyncio
async def test_fixed_briefs_return_single_relevant_records():
    path = Path(__file__).resolve().parents[1] / "evidence" / "baseline" / "briefs.json"
    for brief in json.loads(path.read_text()):
        result = await direct(brief["brief"])
        assert result["direction"]["surface"] == brief["surface"], result
        assert result["questions"] == []
        assert len(json.dumps(result, ensure_ascii=False)) <= 6000
        assert "tags" not in result["direction"]
        assert result["interaction"]["accent_foreground"] in (
            result["direction"]["palette"]["ink"], result["direction"]["palette"]["paper"],
        )


@pytest.mark.asyncio
async def test_vague_request_has_a_default_and_rejection_is_explicit():
    result = await direct("Make it beautiful.")
    assert result["direction"]["surface"] == "landing"
    assert result["questions"][0]["default"] in result["questions"][0]["options"]
    selected = result["direction"]["id"]
    avoid = [row.id for row in library().values() if row.surface == "landing"]
    assert selected in avoid
    assert "error" in await direct("Make it beautiful.", avoid=avoid)
    assert "error" in await direct(" ")


@pytest.mark.asyncio
async def test_stage_turnaround_and_dispatch_get_distinct_directions():
    theatre = await direct("Make it feel premium. The stage manager needs to see which rehearsal room is late.")
    logistics = await direct("Dispatch board for a dispatcher tracking a late load.")
    assert theatre["direction"]["id"] == "stage-call-sheet"
    assert logistics["direction"]["id"] == "exception-first"
    assert theatre["questions"] == []
    alternate = await direct("Theatre turnaround board", avoid=["stage-call-sheet"])
    assert alternate["direction"]["id"] == "exception-first"


@pytest.mark.asyncio
async def test_reactions_have_visible_deltas_with_bounded_responses():
    for direction in library().values():
        calmer = await react(direction.id, "Calmer.")
        bolder = await react(direction.id, "bolder")
        generic = await react(direction.id, "too generic")
        assert calmer["changes"]["type_ratio"] <= direction.type.ratio <= bolder["changes"]["type_ratio"]
        assert "spacing" in calmer["changes"] and "composition" in bolder["changes"]
        assert direction.layout.focus in generic["changes"]["composition"]
        assert len(json.dumps(generic, ensure_ascii=False)) <= 3200
        assert (await react(direction.id, "more like A"))["needs_comparison"]


@pytest.mark.asyncio
async def test_source_tool_is_bounded_and_exposes_render_scope():
    result = await check("<button>Get started</button>\n" * 500)
    assert result["finding_count"] == 500
    assert result["truncated"] and result["render_checks"]
    assert len(json.dumps(result, ensure_ascii=False)) <= 2400


@pytest.mark.asyncio
async def test_held_out_briefs_infer_surface_without_clarification():
    path = Path(__file__).resolve().parents[1] / "evidence" / "rebuild" / "spec" / "held-out.json"
    for case in json.loads(path.read_text()):
        result = await direct(case["brief"])
        assert result["direction"]["surface"] == case["surface"], case["id"]
        assert not result["questions"]
        assert (await react(result["direction"]["id"], "too generic"))["changes"]["composition"]


@pytest.mark.asyncio
@pytest.mark.parametrize(("brief", "expected"), [
    ("Landing page for a volunteer radio station. Show the presenter and let me listen live.", "broadcast-board"),
    ("An independent repair shop takes bookings for bicycle wheel truing. Build a site with a quote and day selector.",
     "service-work-order"),
    ("Launch a pocket radio for $60. Show the single product with a button to add it to the bag.", "object-hero"),
])
async def test_landing_uses_the_primary_task_for_art_direction(brief, expected):
    result = await direct(brief, surface="landing")
    assert result["direction"]["id"] == expected
    assert not result["questions"]
    if expected != "object-hero":
        assert (await direct(brief, surface="landing", avoid=[expected]))["direction"]["id"] == "object-hero"
