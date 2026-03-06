"""Tests for all 6 MCP server tools."""
import asyncio
import json
import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_db(populated_db):
    """Patch the server's db with our test database."""
    import server
    original_db = server.db
    server.db = populated_db
    yield populated_db
    server.db = original_db


class TestSearchDesignPatterns:
    @pytest.mark.asyncio
    async def test_basic_search(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="dashboard")
        assert isinstance(results, list)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_returns_blueprints(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="stripe")
        assert len(results) >= 1
        bp = results[0]
        assert "id" in bp
        assert "name" in bp
        assert "page_type" in bp

    @pytest.mark.asyncio
    async def test_search_with_page_type_filter(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="", page_type="Dashboard")
        assert all(r["page_type"] == "Dashboard" for r in results)

    @pytest.mark.asyncio
    async def test_search_with_color_mode(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="", color_mode="dark")
        assert len(results) == 1
        assert results[0]["color_mode"] == "dark"

    @pytest.mark.asyncio
    async def test_search_with_fields_filter(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(
            query="dashboard", fields=["name", "page_type"]
        )
        assert len(results) >= 1
        for r in results:
            assert "id" in r  # id always included
            assert "name" in r
            # Fields not requested should be absent
            assert "behavioral_description" not in r

    @pytest.mark.asyncio
    async def test_search_limit(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="", limit=1)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, mock_db):
        from server import search_design_patterns
        results = await search_design_patterns(query="xyznonexistent")
        assert results == []


class TestGetDesignBlueprint:
    @pytest.mark.asyncio
    async def test_get_existing(self, mock_db):
        from server import get_design_blueprint
        result = await get_design_blueprint("test-curated-001")
        assert result["id"] == "test-curated-001"
        assert "name" in result

    @pytest.mark.asyncio
    async def test_get_missing(self, mock_db):
        from server import get_design_blueprint
        result = await get_design_blueprint("nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_detailed(self, mock_db):
        from server import get_design_blueprint
        result = await get_design_blueprint("test-curated-001", detailed=True)
        # Detailed should include all fields
        assert "accessibility_notes" in result
        assert "semantic_tokens" in result
        assert "component_hints" in result

    @pytest.mark.asyncio
    async def test_get_condensed(self, mock_db):
        from server import get_design_blueprint
        result = await get_design_blueprint("test-curated-001", detailed=False)
        # Condensed blueprint should include actionable data
        assert "name" in result
        assert "page_type" in result
        # Now includes component_hints, accessibility_notes, semantic_tokens
        assert "component_hints" in result
        assert "accessibility_notes" in result


class TestGetSemanticTokens:
    @pytest.mark.asyncio
    async def test_returns_tokens(self):
        from server import get_semantic_tokens
        tokens = await get_semantic_tokens()
        assert isinstance(tokens, dict)
        assert len(tokens) > 0

    @pytest.mark.asyncio
    async def test_returns_tokens_with_style(self):
        from server import get_semantic_tokens
        tokens = await get_semantic_tokens(style="dark")
        assert isinstance(tokens, dict)


class TestGetDesignTaxonomy:
    @pytest.mark.asyncio
    async def test_returns_taxonomy(self):
        from server import get_design_taxonomy
        taxonomy = await get_design_taxonomy()
        assert isinstance(taxonomy, dict)
        assert "page_types" in taxonomy

    @pytest.mark.asyncio
    async def test_taxonomy_has_elements(self):
        from server import get_design_taxonomy
        taxonomy = await get_design_taxonomy()
        assert len(taxonomy["page_types"]) > 0


class TestGetBehavioralPattern:
    @pytest.mark.asyncio
    async def test_exact_match(self):
        from server import get_behavioral_pattern
        result = await get_behavioral_pattern("empty_state")
        assert "description" in result
        assert "best_practice" in result

    @pytest.mark.asyncio
    async def test_fuzzy_match(self):
        from server import get_behavioral_pattern
        result = await get_behavioral_pattern("loading")
        assert "skeleton_loading" in result

    @pytest.mark.asyncio
    async def test_unknown_pattern(self):
        from server import get_behavioral_pattern
        result = await get_behavioral_pattern("xyznonexistent")
        assert "error" in result
        assert "available" in result

    @pytest.mark.asyncio
    async def test_all_behavioral_patterns(self):
        from server import get_behavioral_pattern
        patterns = ["empty_state", "skeleton_loading", "error_handling",
                     "onboarding_flow", "form_validation", "infinite_scroll",
                     "command_palette"]
        for name in patterns:
            result = await get_behavioral_pattern(name)
            assert "description" in result


class TestCompareDesignApproaches:
    @pytest.mark.asyncio
    async def test_compare_returns_structure(self, mock_db):
        from server import compare_design_approaches
        result = await compare_design_approaches("Dashboard")
        assert "page_type" in result
        assert "examples" in result
        assert "summary" in result
        assert result["page_type"] == "Dashboard"

    @pytest.mark.asyncio
    async def test_compare_examples_are_blueprints(self, mock_db):
        from server import compare_design_approaches
        result = await compare_design_approaches("Dashboard")
        for ex in result["examples"]:
            assert "id" in ex
            assert "name" in ex

    @pytest.mark.asyncio
    async def test_compare_no_results(self, mock_db):
        from server import compare_design_approaches
        result = await compare_design_approaches("404 Page")
        assert result["examples"] == []
        assert "No patterns found" in result["summary"]

    @pytest.mark.asyncio
    async def test_compare_limit(self, mock_db):
        from server import compare_design_approaches
        result = await compare_design_approaches("Dashboard", limit=1)
        assert len(result["examples"]) <= 1
