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


@pytest.mark.parametrize(("brief", "expected"), [
    ("A form.", "grouped-fieldsets"),
    ("A form a volunteer can finish after work.", "grouped-fieldsets"),
    ("A mobile signup for a ceramics class. Collect name and email.", "grouped-fieldsets"),
    ("Let tenants apply for a parking permit from a phone.", "grouped-fieldsets"),
    ("On mobile, staff need a way to request replacement tools.", "grouped-fieldsets"),
    ("Request replacement tools.", "grouped-fieldsets"),
    ("Help volunteers file a travel reimbursement request.", "grouped-fieldsets"),
    ("Make a portfolio submission form for artists.", "grouped-fieldsets"),
    ("Give me one question on a form to check eligibility.", "question-column"),
    ("Neighbors can vote on a meeting time on their phones.", "question-column"),
    ("A sign-up asking for email only.", "question-column"),
    ("A single-field screen for a reader's suggestion.", "question-column"),
    ("Collect a group contact, email, group size and choice of tour on a form.", "grouped-fieldsets"),
    ("On a form, record the account name and one choice of delivery channel.", "grouped-fieldsets"),
    ("Collect a bag weight and a drop-off location, then show confirmation.", "grouped-fieldsets"),
    ("Ask for pickup day and item quantity. Keep entries on invalid submission.", "grouped-fieldsets"),
])
@pytest.mark.asyncio
async def test_primary_entry_task_selects_a_form(brief, expected):
    result = await direct(brief)
    assert result["direction"]["surface"] == "form"
    assert result["direction"]["id"] == expected
    assert result["questions"] == []
    assert "tags" not in result["direction"]
    assert len(json.dumps(result, ensure_ascii=False).encode("utf-8")) <= 6000


@pytest.mark.parametrize(("brief", "expected"), [
    ("A landing page with a request form in the footer.", "landing"),
    ("A signup landing page for a local club.", "landing"),
    ("A portfolio featuring a signup for studio news.", "portfolio"),
    ("A dashboard to review applications and survey results.", "dashboard"),
    ("A registration dashboard that includes a contact form.", "dashboard"),
    ("Request latency dashboard with a time range control.", "dashboard"),
    ("An article explaining how to apply for a fellowship.", "editorial"),
    ("A long-form field report.", "editorial"),
    ("Show the new phone form factor on a product page.", "landing"),
    ("Compare plans by API request volume.", "pricing"),
    ("Apply filters to the work queue of pull requests.", "dashboard"),
    ("Apply to all rows of a table.", "dashboard"),
    ("A supervisor's work queue showing completed forms.", "dashboard"),
    ("A mobile ticket with a sign-in link.", "mobile"),
    ("An analytics platform to report completion rates.", "dashboard"),
    ("A dashboard where analysts enter a time range and review invalid receipts.", "dashboard"),
])
@pytest.mark.asyncio
async def test_forms_as_secondary_content_or_compounds_keep_existing_route(brief, expected):
    assert (await direct(brief))["direction"]["surface"] == expected


@pytest.mark.asyncio
async def test_explicit_surfaces_and_form_controls():
    brief = "A mobile form to choose a callback time."
    records = library()
    for surface in {record.surface for record in records.values()}:
        result = await direct(brief, surface=surface)
        assert result["direction"]["surface"] == surface
        assert result["questions"] == []

    assert (await direct("An editorial home.", surface="form"))["direction"]["surface"] == "form"
    selected = (await direct(brief))["direction"]["id"]
    other = (await direct(brief, avoid=[selected]))["direction"]["id"]
    assert {selected, other} == {"question-column", "grouped-fieldsets"}
    exhausted = await direct(brief, avoid=[selected, other])
    assert exhausted["surface"] == "form" and "error" in exhausted
    comparison = await react(selected, "more like A", comparison_id=other)
    assert comparison["changes"]["composition"] == records[other].layout.skeleton
    assert "error" in await react(selected, "more like A", comparison_id="object-hero")


@pytest.mark.parametrize(("record_id", "source_url"), [
    ("question-column", "https://design-system.service.gov.uk/patterns/question-pages/#start-by-asking-one-question-per-page"),
    ("grouped-fieldsets", "https://designsystem.digital.gov/templates/form-templates/#accessibility-guidance"),
])
def test_form_records_credit_the_guidance_behind_the_layout(record_id, source_url):
    record = library()[record_id]
    assert any(source.url == source_url and source.strength == "evidence" for source in record.sources)
    assert "390px" in record.layout.mobile


@pytest.mark.asyncio
async def test_reactions_have_visible_deltas_with_bounded_responses():
    for direction in library().values():
        calmer = await react(direction.id, "Calmer.")
        bolder = await react(direction.id, "bolder")
        generic = await react(direction.id, "too generic")
        if direction.surface == "form":
            assert set(calmer["changes"]) == {"spacing"}
            assert "24px" in direction.layout.rhythm and "24px to 32px" in calmer["changes"]["spacing"]
            assert direction.layout.focus in calmer["keep"] and "primary action and its current label" in calmer["keep"]
        else:
            assert calmer["changes"]["type_ratio"] <= direction.type.ratio
        assert bolder["changes"]["type_ratio"] >= direction.type.ratio
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


@pytest.mark.asyncio
async def test_constraint_comparison_requires_alternatives_height_and_swing():
    brief = (
        "Make the town tool library site for a first-time borrower who needs a PH2 tool tonight. "
        "The cabinet has 42 ±1 mm between the screw and the face rail, and a cleat limits swing to 12°. "
        "The desk is open 18:00–19:00. The borrower can arrive from 18:10. "
        "Stubby is 45–46 mm with direct drive and ready 18:00. Flat is 27–28 mm, needs 15° to reset "
        "and is ready 18:00. Pocket is 37–38 mm, needs 10° and is ready 18:00. Fine is 31–32 mm, "
        "needs 6° and is ready 18:25. A selected Pocket is withdrawn at 17:56 because the ratchet jams; "
        "let the visitor choose the replacement."
    )
    assert (await direct(brief))["direction"]["id"] == "constraint-comparison"
    assert (await direct(brief, surface="landing"))["direction"]["id"] == "constraint-comparison"
    assert (await direct(brief, surface="dashboard"))["direction"]["surface"] == "dashboard"
    assert (await direct(brief, avoid=["constraint-comparison"]))["direction"]["id"] != "constraint-comparison"


@pytest.mark.asyncio
@pytest.mark.parametrize("brief", [
    "Compare tool height against 42 mm of clearance and choose a tool.",
    "Replace the ratchet tool; it needs 10 degrees of swing.",
    "Choose a 42 mm tool from the library.",
    "Launch a landing page. Choose a finish for a 41 mm radio with a tilting stand that adjusts to 12 degrees.",
])
async def test_constraint_comparison_rejects_missing_orthogonal_cues(brief):
    assert (await direct(brief))["direction"]["id"] != "constraint-comparison"


@pytest.mark.asyncio
async def test_access_window_requires_step_free_route_and_train_cutoff():
    brief = (
        "Help me choose a recovery route after the step-free entrance changed so I can catch the 18:42 train. "
        "Show the route, clock time and signed minutes remaining before departure."
    )
    assert (await direct(brief))["direction"]["id"] == "access-window"
    assert (await direct(brief, surface="landing"))["direction"]["id"] == "access-window"
    assert (await direct(brief, surface="mobile"))["direction"]["surface"] == "mobile"
    assert (await direct(brief, avoid=["access-window"]))["direction"]["id"] != "access-window"


@pytest.mark.asyncio
@pytest.mark.parametrize("brief", [
    "Plan a step-free route to a recital with no deadline.",
    "Show live train departure boards and platform times.",
    "Help me catch the 18:42 train by choosing a route.",
    "Choose a step-free route to the venue without a train cutoff.",
    "Build a board to choose a step-free station and display the 18:42 train for information.",
])
async def test_access_window_rejects_attendance_or_unrelated_departure_claims(brief):
    assert (await direct(brief))["direction"]["id"] != "access-window"


@pytest.mark.asyncio
async def test_experimental_records_stay_out_of_ordinary_landing_scoring():
    ordinary = await direct("A landing page for a small-batch soap shop.")
    assert ordinary["direction"]["id"] not in {"constraint-comparison", "access-window"}
    for record_id in ("constraint-comparison", "access-window"):
        assert library()[record_id].surface == "landing"


@pytest.mark.asyncio
@pytest.mark.parametrize("reaction", ["calmer", "Quieter!", "more calm", "less loud"])
async def test_calmer_keeps_the_operational_exception_as_the_focal_point(reaction):
    result = await react("exception-first", reaction)
    accent = result["changes"]["accent_usage"]
    assert "urgent exception as the strongest accent" in accent
    assert "its status in the queue" in accent
    assert "secondary controls" in accent
    assert "status labeled in words" in accent
