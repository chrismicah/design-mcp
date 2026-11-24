import pytest

from follow_up import next_reaction


@pytest.fixture
def initial():
    draft = {"case": "pricing-misleading", "arm": "plain", "status": "passed",
             "source_commit": None, "usage": {"input_tokens": 10}, "html_sha256": "draft"}
    ballot = {"case": "pricing-misleading", "verified_screens": 4, "required_screens": 4, "screens": {
        "A-1440": {"arm": "plain", "html_sha256": "draft", "weighted": 9.5},
        "A-390": {"arm": "plain", "html_sha256": "draft", "weighted": 8.75},
        "B-1440": {"arm": "design-mcp", "html_sha256": "other", "weighted": 8.5},
        "B-390": {"arm": "design-mcp", "html_sha256": "other", "weighted": 8.0},
    }}
    return draft, ballot, "pricing-misleading", "plain"


def test_reactions_follow_the_sealed_order_and_stop_after_two(initial):
    draft, *_ = initial
    assert next_reaction(*initial) == (1, "calmer")
    draft["reaction_number"] = 1
    assert next_reaction(*initial) == (2, "too generic")
    draft["reaction_number"] = 2
    with pytest.raises(ValueError, match="No sealed reaction"):
        next_reaction(*initial)


def test_draft_that_passed_at_both_widths_cannot_be_revised(initial):
    _, ballot, *_ = initial
    ballot["screens"]["A-390"]["weighted"] = 9.5
    with pytest.raises(ValueError, match="already reached"):
        next_reaction(*initial)


def test_stale_ballot_cannot_resume_the_thread(initial):
    _, ballot, *_ = initial
    ballot["screens"]["A-390"]["html_sha256"] = "stale"
    with pytest.raises(ValueError, match="Both ballot views"):
        next_reaction(*initial)
