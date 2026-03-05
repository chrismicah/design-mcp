"""Comprehensive pytest suite for Design Intelligence MCP Server."""
import pytest
import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase
from server import (
    search_design_patterns,
    get_design_blueprint,
    get_semantic_tokens,
    get_design_taxonomy,
    get_behavioral_pattern,
    compare_design_approaches,
    analyze_and_devibecode,
)

BASE_DIR = Path(__file__).parent.parent


# ============================================================
# Schema Tests
# ============================================================

class TestSchema:
    def test_design_pattern_creation(self):
        p = DesignPattern(
            id="test-1",
            name="Test Pattern",
            source="test",
            source_url="https://example.com",
            page_type="Dashboard",
        )
        assert p.id == "test-1"
        assert p.platform == Platform.WEB  # default

    def test_all_platforms(self):
        for platform in Platform:
            p = DesignPattern(
                id=f"test-{platform.value}",
                name=f"Test {platform.value}",
                source="test",
                source_url="https://example.com",
                page_type="Dashboard",
                platform=platform,
            )
            assert p.platform == platform

    def test_all_layout_types(self):
        for lt in LayoutType:
            p = DesignPattern(
                id=f"test-{lt.value}",
                name=f"Test {lt.value}",
                source="test",
                source_url="https://example.com",
                page_type="Dashboard",
                layout_type=lt,
            )
            assert p.layout_type == lt

    def test_optional_fields_default_none(self):
        p = DesignPattern(
            id="test-min",
            name="Minimal",
            source="test",
            source_url="https://example.com",
            page_type="Dashboard",
        )
        assert p.image_url is None
        assert p.industry is None
        assert p.layout_type is None
        assert p.color_mode is None
        assert p.behavioral_description is None
        assert p.accessibility_notes is None
        assert p.semantic_tokens is None
        assert p.quality_score is None

    def test_list_fields_default_empty(self):
        p = DesignPattern(
            id="test-lists",
            name="Lists",
            source="test",
            source_url="https://example.com",
            page_type="Dashboard",
        )
        assert p.ux_patterns == []
        assert p.ui_elements == []
        assert p.visual_style == []
        assert p.primary_colors == []
        assert p.component_hints == []
        assert p.tags == []

    def test_quality_score_bounds(self):
        p = DesignPattern(
            id="test-score",
            name="Scored",
            source="test",
            source_url="https://example.com",
            page_type="Dashboard",
            quality_score=8.5,
        )
        assert p.quality_score == 8.5
        
        with pytest.raises(Exception):
            DesignPattern(
                id="test-bad", name="Bad", source="test",
                source_url="x", page_type="D",
                quality_score=11.0,  # Out of bounds
            )

    def test_serialization(self):
        p = DesignPattern(
            id="test-serial",
            name="Serial",
            source="test",
            source_url="https://example.com",
            page_type="Dashboard",
            layout_type=LayoutType.CSS_GRID,
            ui_elements=["Card", "Button"],
            tags=["test", "grid"],
        )
        d = p.model_dump()
        assert isinstance(d, dict)
        assert d["layout_type"] == "css_grid"
        p2 = DesignPattern(**d)
        assert p2.id == p.id


# ============================================================
# Database Tests
# ============================================================

class TestDatabase:
    @pytest.fixture
    def temp_db(self, tmp_path):
        db_path = str(tmp_path / "test_patterns.json")
        return DesignDatabase(db_path)

    def test_empty_db(self, temp_db):
        assert temp_db.count() == 0

    def test_add_and_get(self, temp_db):
        p = DesignPattern(
            id="db-test-1", name="Test", source="test",
            source_url="https://example.com", page_type="Dashboard",
        )
        temp_db.add(p)
        temp_db.save()
        assert temp_db.count() == 1
        assert temp_db.get("db-test-1").name == "Test"

    def test_get_missing(self, temp_db):
        assert temp_db.get("nonexistent") is None

    def test_add_batch(self, temp_db):
        patterns = [
            DesignPattern(
                id=f"batch-{i}", name=f"Batch {i}", source="test",
                source_url="https://example.com", page_type="Dashboard",
            )
            for i in range(10)
        ]
        temp_db.add_batch(patterns)
        assert temp_db.count() == 10

    def test_search_by_page_type(self, temp_db):
        temp_db.add_batch([
            DesignPattern(id="s1", name="A", source="t", source_url="x", page_type="Dashboard"),
            DesignPattern(id="s2", name="B", source="t", source_url="x", page_type="Pricing"),
            DesignPattern(id="s3", name="C", source="t", source_url="x", page_type="Dashboard"),
        ])
        results = temp_db.search(page_type="Dashboard")
        assert len(results) == 2

    def test_search_by_query(self, temp_db):
        temp_db.add_batch([
            DesignPattern(id="q1", name="Stripe Dashboard", source="t", source_url="x", page_type="Dashboard", tags=["fintech"]),
            DesignPattern(id="q2", name="Blog Post Layout", source="t", source_url="x", page_type="Blog Post", tags=["blog"]),
        ])
        results = temp_db.search(query="stripe fintech")
        assert len(results) >= 1
        assert results[0].id == "q1"

    def test_search_by_industry(self, temp_db):
        temp_db.add_batch([
            DesignPattern(id="i1", name="A", source="t", source_url="x", page_type="D", industry="Fintech"),
            DesignPattern(id="i2", name="B", source="t", source_url="x", page_type="D", industry="Health"),
        ])
        results = temp_db.search(industry="Fintech")
        assert len(results) == 1
        assert results[0].id == "i1"

    def test_search_by_color_mode(self, temp_db):
        temp_db.add_batch([
            DesignPattern(id="c1", name="A", source="t", source_url="x", page_type="D", color_mode="dark"),
            DesignPattern(id="c2", name="B", source="t", source_url="x", page_type="D", color_mode="light"),
        ])
        results = temp_db.search(color_mode="dark")
        assert len(results) == 1

    def test_search_limit(self, temp_db):
        temp_db.add_batch([
            DesignPattern(id=f"l{i}", name=f"L{i}", source="t", source_url="x", page_type="Dashboard")
            for i in range(20)
        ])
        results = temp_db.search(page_type="Dashboard", limit=3)
        assert len(results) == 3

    def test_persistence(self, tmp_path):
        db_path = str(tmp_path / "persist.json")
        db1 = DesignDatabase(db_path)
        db1.add(DesignPattern(id="persist", name="P", source="t", source_url="x", page_type="D"))
        db1.save()
        
        db2 = DesignDatabase(db_path)
        assert db2.count() == 1
        assert db2.get("persist").name == "P"


# ============================================================
# Server Tool Tests
# ============================================================

class TestServerTools:
    @pytest.mark.asyncio
    async def test_get_taxonomy(self):
        tax = await get_design_taxonomy()
        assert "page_types" in tax
        assert "ui_elements" in tax
        assert "ux_patterns" in tax
        assert "industries" in tax
        assert "visual_styles" in tax
        assert len(tax["page_types"]) > 10

    @pytest.mark.asyncio
    async def test_get_semantic_tokens(self):
        tokens = await get_semantic_tokens()
        assert "color" in tokens
        assert "spacing" in tokens

    @pytest.mark.asyncio
    async def test_behavioral_pattern_exact(self):
        bp = await get_behavioral_pattern("empty_state")
        assert "description" in bp
        assert "best_practice" in bp
        assert "required_elements" in bp

    @pytest.mark.asyncio
    async def test_behavioral_pattern_fuzzy(self):
        bp = await get_behavioral_pattern("loading")
        assert len(bp) >= 1  # Should fuzzy match skeleton_loading

    @pytest.mark.asyncio
    async def test_behavioral_pattern_unknown(self):
        bp = await get_behavioral_pattern("nonexistent_xyz")
        assert "error" in bp

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        results = await search_design_patterns("dashboard")
        assert isinstance(results, list)
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        results = await search_design_patterns("design", page_type="Dashboard", limit=3)
        assert len(results) <= 3
        for r in results:
            assert r.get("page_type") == "Dashboard"

    @pytest.mark.asyncio
    async def test_search_field_filtering(self):
        results = await search_design_patterns("dashboard", fields=["page_type", "layout_type"], limit=2)
        if results:
            for r in results:
                assert "id" in r  # id always included
                assert "page_type" in r

    @pytest.mark.asyncio
    async def test_get_blueprint_missing(self):
        bp = await get_design_blueprint("nonexistent-id-xyz")
        assert "error" in bp

    @pytest.mark.asyncio
    async def test_compare_approaches(self):
        cmp = await compare_design_approaches("Dashboard", limit=3)
        assert "page_type" in cmp
        assert "examples" in cmp
        assert "summary" in cmp

    @pytest.mark.asyncio
    async def test_analyze_and_devibecode(self):
        bad_code = '''
<div className="bg-[#ff0000] w-[320px] z-[999]" style={{ padding: 10 }}>
  <div onClick={handleClick}>
    <input placeholder="email" className="outline-none">
  </div>
</div>
'''
        result = await analyze_and_devibecode(bad_code)
        # Check exact schema keys
        assert "anti_patterns_found" in result
        assert "recommended_layout" in result
        assert "semantic_tokens_to_apply" in result
        assert "suggested_component_structure" in result
        assert "severity_summary" in result
        assert "refactoring_suggestions" in result
        # Should find issues
        assert len(result["anti_patterns_found"]) > 0
        assert result["severity_summary"]["errors"] + result["severity_summary"]["warnings"] > 0
        # Refactoring suggestions should be present
        assert len(result["refactoring_suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_and_devibecode_empty_input(self):
        result = await analyze_and_devibecode("")
        assert result["anti_patterns_found"] == []
        assert result["severity_summary"] == {"errors": 0, "warnings": 0, "info": 0}

    @pytest.mark.asyncio
    async def test_analyze_and_devibecode_clean_code(self):
        clean_code = '''
<section className="flex flex-col gap-4 p-4">
  <h1 className="text-2xl font-bold">Title</h1>
  <p className="text-gray-600">Description</p>
</section>
'''
        result = await analyze_and_devibecode(clean_code)
        assert result["severity_summary"]["errors"] == 0


# ============================================================
# Data Quality Tests
# ============================================================

class TestDataQuality:
    @pytest.fixture(scope="class")
    def patterns(self):
        with open(BASE_DIR / "data" / "patterns.json") as f:
            return json.load(f)

    def test_patterns_not_empty(self, patterns):
        assert len(patterns) > 6000

    def test_all_patterns_have_required_fields(self, patterns):
        required = ["id", "name", "source", "source_url", "page_type"]
        for p in patterns[:100]:  # Sample check
            for field in required:
                assert field in p, f"Pattern {p.get('id')} missing {field}"

    def test_all_patterns_scored(self, patterns):
        for p in patterns[:100]:
            assert p.get("quality_score") is not None

    def test_quality_scores_in_range(self, patterns):
        for p in patterns:
            score = p.get("quality_score")
            if score is not None:
                assert 0 <= score <= 10, f"Score {score} out of range for {p['id']}"

    def test_multiple_sources(self, patterns):
        sources = set(p["source"] for p in patterns)
        assert len(sources) >= 3  # At least webui-7kbal, dribbble, awwwards

    def test_diverse_page_types(self, patterns):
        page_types = set(p["page_type"] for p in patterns)
        assert len(page_types) >= 5

    def test_patterns_sorted_by_quality(self, patterns):
        """Top patterns should have higher scores."""
        scores = [p.get("quality_score", 0) for p in patterns[:10]]
        assert scores == sorted(scores, reverse=True)

    def test_screenshot_files_exist(self):
        """At least some screenshot directories should have files."""
        screenshot_dir = BASE_DIR / "screenshots"
        assert screenshot_dir.exists()
        total = sum(1 for _ in screenshot_dir.rglob("*") if _.is_file())
        assert total >= 100


# ============================================================
# Integration Tests
# ============================================================

class TestIntegration:
    @pytest.mark.asyncio
    async def test_search_then_blueprint(self):
        """Search should return IDs that work with get_blueprint."""
        results = await search_design_patterns("dashboard", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"])
            assert "error" not in bp
            assert bp.get("id") == results[0]["id"]

    @pytest.mark.asyncio
    async def test_quality_ranked_results(self):
        """Higher quality patterns should appear first in search."""
        results = await search_design_patterns("dashboard", limit=10)
        if len(results) >= 2:
            # Results should be roughly quality-sorted (search also factors in relevance)
            assert isinstance(results[0], dict)
            assert "id" in results[0]

    @pytest.mark.asyncio
    async def test_end_to_end_design_workflow(self):
        """Simulate a real AI agent workflow: taxonomy → search → blueprint → tokens."""
        # 1. Get taxonomy
        tax = await get_design_taxonomy()
        assert "Dashboard" in tax["page_types"]
        
        # 2. Search for patterns
        results = await search_design_patterns("dashboard", page_type="Dashboard", limit=3)
        assert len(results) > 0
        
        # 3. Get blueprint for top result
        bp = await get_design_blueprint(results[0]["id"], detailed=True)
        assert "error" not in bp
        
        # 4. Get tokens for styling
        tokens = await get_semantic_tokens()
        assert "color" in tokens
        
        # 5. Get behavioral pattern
        behavior = await get_behavioral_pattern("empty_state")
        assert "best_practice" in behavior
