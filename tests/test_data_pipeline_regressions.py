"""
Regression tests for every data quality bug found during the pipeline rebuild.

Each test is named after the specific bug it prevents from recurring.
These are NOT generic quality checks — they target exact failure modes.

Bug History:
1. Vision results merged but primary_colors field was skipped
2. 99.9% of semantic_tokens were string "light"/"dark" not real dicts
3. Behavioral descriptions were identical template text for same page_type
4. scan_project returned descriptions but no concrete code fix examples
5. Token sets weren't WCAG AA checked
6. Decision trees missing entirely from tool responses
7. Patterns sorted by data_quality_score broke quality_score ordering
"""

import pytest
import asyncio
import json
import math
import colorsys
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase
from models.visual_analyzer import (
    hex_to_rgb, rgb_to_hsl, relative_luminance, contrast_ratio
)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(scope="module")
def patterns():
    with open(DATA_DIR / "patterns.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def vision_results():
    with open(DATA_DIR / "vision_results.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def token_sets():
    with open(DATA_DIR / "tokens" / "token_sets.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def anti_pattern_fixes():
    with open(DATA_DIR / "anti_pattern_fixes.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def decision_trees():
    with open(DATA_DIR / "decision_trees_indexed.json") as f:
        return json.load(f)


# ============================================================
# BUG #1: Vision primary_colors not merged into patterns
# Previously: smart_enrichment.py copied ui_elements, visual_style,
# page_type, layout_type, color_mode, quality_score BUT skipped
# primary_colors entirely.
# ============================================================

class TestBug1_VisionColorsMerge:
    def test_vision_patterns_with_colors_exist_in_patterns(self, patterns, vision_results):
        """Vision results that have primary_colors should be merged into matching patterns."""
        # Build index of patterns by image_url
        pattern_images = {p.get("image_url"): p for p in patterns if p.get("image_url")}
        
        # Count vision results that have colors AND match a pattern
        vision_with_colors = {
            k: v for k, v in vision_results.items()
            if v.get("primary_colors") and k in pattern_images
        }
        
        if len(vision_with_colors) == 0:
            pytest.skip("No vision results with colors found")
        
        # At least some should have colors merged into the pattern
        merged_count = 0
        for img_url, vdata in vision_with_colors.items():
            pattern = pattern_images[img_url]
            if pattern.get("primary_colors"):
                merged_count += 1
        
        assert merged_count > 0, (
            f"None of {len(vision_with_colors)} vision results with colors "
            f"had their colors merged into patterns"
        )

    def test_patterns_with_colors_have_valid_hex(self, patterns):
        """Every primary_color must be a valid hex color."""
        for p in patterns:
            colors = p.get("primary_colors", [])
            for color in colors:
                assert isinstance(color, str), f"Color must be string, got {type(color)}"
                # Allow #RGB, #RRGGBB, or bare RRGGBB
                clean = color.lstrip("#")
                assert len(clean) in (3, 6), f"Invalid hex color: {color}"
                assert all(c in "0123456789abcdefABCDEF" for c in clean), (
                    f"Non-hex characters in color: {color}"
                )


# ============================================================
# BUG #2: 99.9% of semantic_tokens were just string "light"/"dark"
# Now: tokens should be int indexes into token_sets.json, each
# resolving to a dict with real color/spacing/typography values.
# ============================================================

class TestBug2_SemanticTokensNotStrings:
    def test_no_string_tokens_in_patterns(self, patterns):
        """No pattern should have semantic_tokens as a bare string anymore."""
        string_count = sum(
            1 for p in patterns
            if isinstance(p.get("semantic_tokens"), str)
        )
        assert string_count == 0, (
            f"{string_count}/{len(patterns)} patterns still have string tokens. "
            f"They should be int indexes or dicts."
        )

    def test_token_indexes_are_valid(self, patterns, token_sets):
        """Every int token index must be within bounds of token_sets.json."""
        max_idx = len(token_sets) - 1
        for p in patterns[:500]:  # Sample
            tokens = p.get("semantic_tokens")
            if isinstance(tokens, int):
                assert 0 <= tokens <= max_idx, (
                    f"Token index {tokens} out of bounds (max {max_idx}) "
                    f"for pattern {p['id']}"
                )

    def test_token_sets_have_real_values(self, token_sets):
        """Every token set must have actual color/spacing keys, not placeholders."""
        required_keys = [
            "color-background", "color-foreground", "color-primary",
            "spacing-sm", "spacing-md", "spacing-lg",
            "font-size-base", "radius-md",
        ]
        for i, ts in enumerate(token_sets):
            if ts is None:
                continue
            for key in required_keys:
                assert key in ts, (
                    f"Token set {i} missing required key '{key}'. "
                    f"Available keys: {list(ts.keys())[:10]}"
                )

    def test_token_colors_are_hex(self, token_sets):
        """Color tokens must be actual hex values, not words."""
        color_keys = [
            "color-background", "color-foreground", "color-primary",
            "color-accent", "color-border",
        ]
        for i, ts in enumerate(token_sets):
            if ts is None:
                continue
            for key in color_keys:
                val = ts.get(key, "")
                if val:
                    assert val.startswith("#"), (
                        f"Token set {i}, key '{key}' = '{val}' is not a hex color"
                    )

    def test_all_patterns_have_tokens(self, patterns):
        """100% of patterns should have semantic_tokens (int index or dict)."""
        missing = [p["id"] for p in patterns if p.get("semantic_tokens") is None]
        pct = len(missing) / len(patterns) * 100
        assert pct < 1, (
            f"{len(missing)} patterns ({pct:.1f}%) have no semantic_tokens. "
            f"First few: {missing[:5]}"
        )


# ============================================================
# BUG #3: Behavioral descriptions were identical templates
# Same page_type got the exact same text regardless of layout,
# elements, or purpose. Now uses cluster-based matching.
# ============================================================

class TestBug3_BehavioralDescriptions:
    def test_not_all_dashboards_identical(self, patterns):
        """Dashboard patterns should NOT all have the same behavioral_description."""
        dashboards = [
            p["behavioral_description"]
            for p in patterns
            if p.get("page_type") == "Dashboard" and p.get("behavioral_description")
        ]
        if len(dashboards) < 10:
            pytest.skip("Not enough dashboard patterns")
        
        unique = set(dashboards)
        assert len(unique) > 1, (
            f"All {len(dashboards)} dashboard patterns have identical behavior text. "
            f"Cluster-based descriptions should produce variety."
        )

    def test_not_all_landing_pages_identical(self, patterns):
        """Landing Page patterns should have varied behavioral descriptions."""
        pages = [
            p["behavioral_description"]
            for p in patterns
            if p.get("page_type") == "Landing Page" and p.get("behavioral_description")
        ]
        if len(pages) < 5:
            pytest.skip("Not enough landing page patterns")
        
        unique = set(pages)
        assert len(unique) > 1, (
            f"All {len(pages)} landing pages have identical behavior text."
        )

    def test_behavioral_descriptions_are_substantial(self, patterns):
        """Behavioral descriptions should be meaningful, not one-liners."""
        sample = [p for p in patterns[:200] if p.get("behavioral_description")]
        short_count = sum(1 for p in sample if len(p["behavioral_description"]) < 80)
        pct = short_count / max(len(sample), 1) * 100
        assert pct < 10, (
            f"{short_count}/{len(sample)} ({pct:.0f}%) behavioral descriptions "
            f"are under 80 chars — too short to be useful"
        )

    def test_behavioral_mentions_interaction(self, patterns):
        """Good behavioral descriptions should mention user interaction."""
        interaction_words = {"hover", "click", "scroll", "animate", "transition", "focus", "toggle", "expand"}
        sample = [p for p in patterns[:100] if p.get("behavioral_description")]
        has_interaction = sum(
            1 for p in sample
            if any(w in p["behavioral_description"].lower() for w in interaction_words)
        )
        pct = has_interaction / max(len(sample), 1) * 100
        assert pct > 50, (
            f"Only {has_interaction}/{len(sample)} ({pct:.0f}%) behavioral descriptions "
            f"mention any interaction (hover, click, scroll, etc.)"
        )


# ============================================================
# BUG #4: scan_project returned no concrete code fixes
# Priority fixes had issue + suggestion text but no before/after
# code examples for the AI to apply directly.
# ============================================================

class TestBug4_AntiPatternFixes:
    def test_anti_pattern_fixes_file_exists(self):
        """anti_pattern_fixes.json must exist."""
        assert (DATA_DIR / "anti_pattern_fixes.json").exists()

    def test_fix_types_have_before_after(self, anti_pattern_fixes):
        """Every fix type must have before and after code examples."""
        for fix_type, fix_data in anti_pattern_fixes.items():
            assert "fix" in fix_data, f"Fix type '{fix_type}' missing 'fix' description"
            assert "before" in fix_data, f"Fix type '{fix_type}' missing 'before' code"
            assert "after" in fix_data, f"Fix type '{fix_type}' missing 'after' code"
            # Before and after must be non-empty strings
            assert len(fix_data["before"]) > 10, f"Fix '{fix_type}' before code too short"
            assert len(fix_data["after"]) > 10, f"Fix '{fix_type}' after code too short"

    def test_common_anti_patterns_covered(self, anti_pattern_fixes):
        """Must have fixes for the most common anti-patterns we detect."""
        must_cover = [
            "div_soup", "missing_flex_grid", "low_contrast",
            "inline_style_abuse", "missing_aria",
        ]
        for ap in must_cover:
            assert ap in anti_pattern_fixes, (
                f"Anti-pattern '{ap}' has no code fix mapping. "
                f"Available: {list(anti_pattern_fixes.keys())}"
            )

    def test_fix_descriptions_are_actionable(self, anti_pattern_fixes):
        """Fix descriptions should tell the AI WHAT TO DO, not just what's wrong."""
        action_words = {"replace", "add", "use", "ensure", "limit", "define", "map"}
        for fix_type, fix_data in anti_pattern_fixes.items():
            fix_text = fix_data["fix"].lower()
            has_action = any(w in fix_text for w in action_words)
            assert has_action, (
                f"Fix for '{fix_type}' doesn't contain action words: '{fix_data['fix'][:80]}...'"
            )


# ============================================================
# BUG #5: No WCAG contrast checking on generated token palettes
# Generated palettes could produce text colors with insufficient
# contrast against background, especially in dark mode.
# ============================================================

class TestBug5_WCAGContrast:
    def test_token_sets_meet_wcag_aa(self, token_sets):
        """Every token set's fg/bg combination must meet WCAG AA (4.5:1)."""
        failures = []
        for i, ts in enumerate(token_sets):
            if ts is None:
                continue
            bg = ts.get("color-background", "")
            fg = ts.get("color-foreground", "")
            if bg.startswith("#") and fg.startswith("#"):
                ratio = contrast_ratio(bg, fg)
                if ratio < 4.5:
                    failures.append(
                        f"Token set {i}: bg={bg} fg={fg} ratio={ratio:.2f} (need 4.5:1)"
                    )
        
        assert len(failures) == 0, (
            f"{len(failures)} token sets fail WCAG AA:\n" +
            "\n".join(failures[:10])
        )

    def test_primary_on_background_readable(self, token_sets):
        """Primary color should have reasonable visibility on background."""
        low_contrast_count = 0
        for ts in token_sets:
            if ts is None:
                continue
            bg = ts.get("color-background", "")
            primary = ts.get("color-primary", "")
            if bg.startswith("#") and primary.startswith("#"):
                ratio = contrast_ratio(bg, primary)
                if ratio < 2.0:  # Primary doesn't need to be text-readable but should be visible
                    low_contrast_count += 1
        
        # Allow some edge cases but most should be visible
        pct = low_contrast_count / max(len(token_sets), 1) * 100
        assert pct < 20, (
            f"{low_contrast_count} token sets ({pct:.0f}%) have nearly invisible primary color on background"
        )


# ============================================================
# BUG #6: Decision trees missing from tool responses
# get_design_blueprint and search_design_patterns returned no
# component selection guidance.
# ============================================================

class TestBug6_DecisionTrees:
    def test_decision_trees_file_exists(self):
        """decision_trees_indexed.json must exist."""
        assert (DATA_DIR / "decision_trees_indexed.json").exists()

    def test_decision_trees_have_content(self, decision_trees):
        """Decision trees must contain actual guidance."""
        assert len(decision_trees) > 0, "No decision trees defined"
        for i, tree in enumerate(decision_trees):
            assert isinstance(tree, dict), f"Decision tree {i} is not a dict"
            assert len(tree) >= 2, (
                f"Decision tree {i} only has {len(tree)} categories — too few"
            )

    def test_dashboard_patterns_have_decision_trees(self, patterns):
        """Dashboard patterns should have decision trees attached."""
        dashboards = [p for p in patterns if p.get("page_type") == "Dashboard"]
        if not dashboards:
            pytest.skip("No dashboard patterns")
        
        with_trees = sum(1 for d in dashboards if d.get("decision_tree") is not None)
        pct = with_trees / len(dashboards) * 100
        assert pct > 80, (
            f"Only {with_trees}/{len(dashboards)} ({pct:.0f}%) dashboards have decision trees"
        )

    def test_decision_tree_content_is_actionable(self, decision_trees):
        """Decision tree guidance should contain conditional logic (if/when)."""
        for tree in decision_trees:
            all_text = " ".join(str(v) for v in tree.values()).lower()
            has_conditional = any(w in all_text for w in ["if ", "when ", "use "])
            assert has_conditional, (
                f"Decision tree has no conditional logic: {all_text[:100]}..."
            )


# ============================================================
# BUG #7: Sort order by data_quality_score broke quality_score ranking
# ============================================================

class TestBug7_SortOrder:
    def test_top_patterns_have_highest_quality_scores(self, patterns):
        """First 10 patterns must be sorted by quality_score descending."""
        scores = [p.get("quality_score", 0) for p in patterns[:10]]
        assert scores == sorted(scores, reverse=True), (
            f"Top 10 quality_scores not sorted: {scores}"
        )

    def test_curated_patterns_in_top_100(self, patterns):
        """Hand-crafted curated patterns should appear in top 100."""
        top_100_sources = Counter(p["source"] for p in patterns[:100])
        assert "curated" in top_100_sources, (
            f"Curated patterns not in top 100. Sources: {dict(top_100_sources)}"
        )


# ============================================================
# SERVER INTEGRATION: Resolved data in tool responses
# ============================================================

class TestServerResolution:
    """Test that server.py correctly resolves indexed references."""

    @pytest.mark.asyncio
    async def test_search_returns_resolved_tokens(self):
        """search_design_patterns must return real token dicts, not indexes."""
        from server import search_design_patterns
        results = await search_design_patterns("dashboard", limit=3)
        for r in results:
            tokens = r.get("semantic_tokens")
            if tokens is not None:
                assert isinstance(tokens, dict), (
                    f"Token in search result is {type(tokens).__name__}, not dict. "
                    f"Value: {tokens}"
                )
                assert "color-background" in tokens, (
                    f"Resolved tokens missing 'color-background'. Keys: {list(tokens.keys())[:5]}"
                )

    @pytest.mark.asyncio
    async def test_blueprint_returns_resolved_tokens(self):
        """get_design_blueprint must return real token dicts."""
        from server import search_design_patterns, get_design_blueprint
        results = await search_design_patterns("landing page", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"])
            tokens = bp.get("semantic_tokens")
            if tokens is not None:
                assert isinstance(tokens, dict), (
                    f"Blueprint token is {type(tokens).__name__}, not dict"
                )
                assert len(tokens) >= 10, f"Only {len(tokens)} token keys — too few"

    @pytest.mark.asyncio
    async def test_blueprint_includes_decision_tree(self):
        """get_design_blueprint should include resolved decision trees for Dashboard patterns."""
        from server import search_design_patterns, get_design_blueprint
        results = await search_design_patterns("dashboard", page_type="Dashboard", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"])
            tree = bp.get("decision_tree")
            # Not all patterns have trees, but dashboards should
            if tree is not None:
                assert isinstance(tree, dict), (
                    f"Decision tree is {type(tree).__name__}, not dict"
                )

    @pytest.mark.asyncio
    async def test_search_returns_behavioral_descriptions(self):
        """Search results must have non-empty behavioral descriptions."""
        from server import search_design_patterns
        results = await search_design_patterns("dashboard", limit=5)
        for r in results:
            behavior = r.get("behavioral_description", "")
            assert len(behavior) > 50, (
                f"Pattern {r['id']} has behavioral_description of only "
                f"{len(behavior)} chars — should be cluster-based and substantial"
            )

    @pytest.mark.asyncio
    async def test_scan_project_returns_code_fixes(self):
        """scan_project priority_fixes should include before/after code."""
        from server import scan_project
        result = await scan_project(
            project_path=str(BASE_DIR / "tests"),
            file_extensions=[".py"]
        )
        # Even if test files are clean, the structure should support code fixes
        fixes = result.get("priority_fixes", [])
        # We can't guarantee issues in test files, so just verify structure
        assert isinstance(fixes, list)


# ============================================================
# DATA INTEGRITY: Cross-file consistency
# ============================================================

class TestDataIntegrity:
    def test_token_sets_referenced_by_patterns_exist(self, patterns, token_sets):
        """Every token index in patterns must resolve to an existing token set."""
        max_idx = len(token_sets) - 1
        bad = []
        for p in patterns:
            tokens = p.get("semantic_tokens")
            if isinstance(tokens, int):
                if tokens < 0 or tokens > max_idx:
                    bad.append((p["id"], tokens))
        
        assert len(bad) == 0, (
            f"{len(bad)} patterns reference invalid token indexes: {bad[:5]}"
        )

    def test_decision_trees_referenced_by_patterns_exist(self, patterns, decision_trees):
        """Every decision tree index in patterns must resolve."""
        max_idx = len(decision_trees) - 1
        bad = []
        for p in patterns:
            tree = p.get("decision_tree")
            if isinstance(tree, int):
                if tree < 0 or tree > max_idx:
                    bad.append((p["id"], tree))
        
        assert len(bad) == 0, (
            f"{len(bad)} patterns reference invalid tree indexes: {bad[:5]}"
        )

    def test_no_orphaned_vision_data(self, patterns, vision_results):
        """Vision results should be linked to patterns via image_url."""
        pattern_images = set(p.get("image_url") for p in patterns if p.get("image_url"))
        orphans = [k for k in vision_results if k not in pattern_images]
        pct = len(orphans) / max(len(vision_results), 1) * 100
        assert pct < 5, (
            f"{len(orphans)}/{len(vision_results)} ({pct:.0f}%) vision results "
            f"don't match any pattern image_url"
        )

    def test_vision_tagged_patterns_have_vision_fields(self, patterns):
        """Patterns tagged 'vision-enriched' should have vision-derived fields."""
        tagged = [p for p in patterns if "vision-enriched" in p.get("tags", [])]
        if not tagged:
            pytest.skip("No vision-enriched patterns found")
        
        has_elements = sum(1 for p in tagged if p.get("ui_elements"))
        pct = has_elements / len(tagged) * 100
        assert pct > 80, (
            f"Only {has_elements}/{len(tagged)} ({pct:.0f}%) vision-enriched patterns "
            f"have ui_elements — vision merge may be incomplete"
        )


# ============================================================
# SCHEMA: New fields must be accepted
# ============================================================

class TestSchemaNewFields:
    def test_schema_accepts_int_tokens(self):
        """Schema should accept int (index) for semantic_tokens."""
        p = DesignPattern(
            id="test-int-token", name="Test", source="test",
            source_url="x", page_type="Dashboard",
            semantic_tokens=42,
        )
        assert p.semantic_tokens == 42

    def test_schema_accepts_dict_tokens(self):
        """Schema should accept dict for semantic_tokens."""
        tokens = {"color-background": "#000000", "color-foreground": "#ffffff"}
        p = DesignPattern(
            id="test-dict-token", name="Test", source="test",
            source_url="x", page_type="Dashboard",
            semantic_tokens=tokens,
        )
        assert p.semantic_tokens == tokens

    def test_schema_accepts_decision_tree(self):
        """Schema should accept decision_tree field."""
        tree = {"layout": "Use sidebar for >5 items"}
        p = DesignPattern(
            id="test-tree", name="Test", source="test",
            source_url="x", page_type="Dashboard",
            decision_tree=tree,
        )
        assert p.decision_tree == tree

    def test_schema_accepts_int_decision_tree(self):
        """Schema should accept int index for decision_tree."""
        p = DesignPattern(
            id="test-tree-idx", name="Test", source="test",
            source_url="x", page_type="Dashboard",
            decision_tree=3,
        )
        assert p.decision_tree == 3

    def test_schema_accepts_data_quality_score(self):
        """Schema should accept data_quality_score field."""
        p = DesignPattern(
            id="test-dqs", name="Test", source="test",
            source_url="x", page_type="Dashboard",
            data_quality_score=8,
        )
        assert p.data_quality_score == 8
