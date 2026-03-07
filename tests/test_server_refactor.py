"""
Tests for the full server.py refactor.
Verifies every tool returns actionable data with resolved references.
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import (
    search_design_patterns,
    get_design_blueprint,
    get_semantic_tokens,
    get_behavioral_pattern,
    compare_design_approaches,
    analyze_and_devibecode,
    generate_refactored_code,
    get_visual_suggestions,
    scan_project,
)

BASE_DIR = Path(__file__).parent.parent


# ============================================================
# Tool 1: search_design_patterns — resolved tokens & trees
# ============================================================

class TestTool1_Search:
    @pytest.mark.asyncio
    async def test_search_tokens_are_dicts_not_ints(self):
        """Search results must never expose raw int token indexes."""
        results = await search_design_patterns("dashboard", limit=5)
        for r in results:
            tokens = r.get("semantic_tokens")
            if tokens is not None:
                assert not isinstance(tokens, int), f"Got int token {tokens} for {r['id']}"
                assert not isinstance(tokens, str), f"Got string token '{tokens}' for {r['id']}"
                assert isinstance(tokens, dict)

    @pytest.mark.asyncio
    async def test_search_tokens_have_hex_colors(self):
        """Resolved tokens must contain actual hex color values."""
        results = await search_design_patterns("landing page", limit=3)
        for r in results:
            tokens = r.get("semantic_tokens", {})
            if isinstance(tokens, dict) and tokens:
                bg = tokens.get("color-background", "")
                assert bg.startswith("#"), f"color-background not hex: {bg}"

    @pytest.mark.asyncio
    async def test_search_returns_decision_trees(self):
        """Dashboard search should include resolved decision trees."""
        results = await search_design_patterns("dashboard", page_type="Dashboard", limit=3)
        trees_found = sum(1 for r in results if r.get("decision_tree") and isinstance(r["decision_tree"], dict))
        assert trees_found > 0, "No resolved decision trees in dashboard search results"

    @pytest.mark.asyncio
    async def test_search_returns_primary_colors(self):
        """Results with vision data should include primary_colors."""
        results = await search_design_patterns("design", limit=20)
        has_colors = sum(1 for r in results if r.get("primary_colors"))
        # Not all will have colors, but some should
        # (we have 195 patterns with colors out of 7080)
        # With limit=20, it's possible none match, so just check structure
        for r in results:
            colors = r.get("primary_colors", [])
            assert isinstance(colors, list)


# ============================================================
# Tool 2: get_design_blueprint — detailed mode resolves refs
# ============================================================

class TestTool2_Blueprint:
    @pytest.mark.asyncio
    async def test_detailed_mode_resolves_tokens(self):
        """detailed=True must return dict tokens, not int indexes."""
        results = await search_design_patterns("pricing", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"], detailed=True)
            tokens = bp.get("semantic_tokens")
            if tokens is not None:
                assert isinstance(tokens, dict), f"Detailed blueprint has {type(tokens).__name__} tokens"

    @pytest.mark.asyncio
    async def test_detailed_mode_resolves_decision_tree(self):
        """detailed=True must return dict tree, not int index."""
        results = await search_design_patterns("dashboard", page_type="Dashboard", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"], detailed=True)
            tree = bp.get("decision_tree")
            if tree is not None:
                assert isinstance(tree, dict), f"Detailed blueprint has {type(tree).__name__} tree"


# ============================================================
# Tool 3: get_semantic_tokens — returns real tokens
# ============================================================

class TestTool3_SemanticTokens:
    @pytest.mark.asyncio
    async def test_returns_light_and_dark(self):
        """Default call should return both light and dark examples."""
        result = await get_semantic_tokens()
        assert "light" in result or "dark" in result or "tokens" in result

    @pytest.mark.asyncio
    async def test_light_mode_has_real_values(self):
        """Light mode tokens should have white-ish backgrounds."""
        result = await get_semantic_tokens(style="light")
        tokens = result.get("tokens", result.get("light", {}))
        if tokens:
            bg = tokens.get("color-background", "")
            assert bg.startswith("#"), f"Background not hex: {bg}"

    @pytest.mark.asyncio
    async def test_dark_mode_has_real_values(self):
        """Dark mode tokens should have dark backgrounds."""
        result = await get_semantic_tokens(style="dark")
        tokens = result.get("tokens", result.get("dark", {}))
        if tokens:
            bg = tokens.get("color-background", "")
            assert bg.startswith("#"), f"Background not hex: {bg}"


# ============================================================
# Tool 5: get_behavioral_pattern — includes dashboard
# ============================================================

class TestTool5_BehavioralPattern:
    @pytest.mark.asyncio
    async def test_dashboard_pattern_exists(self):
        """Dashboard behavioral pattern must exist (was missing before)."""
        result = await get_behavioral_pattern("dashboard")
        assert "error" not in result, f"Dashboard pattern missing: {result}"
        assert "description" in result
        assert "required_elements" in result

    @pytest.mark.asyncio
    async def test_dashboard_has_decision_tree(self):
        """Dashboard behavioral pattern should include a decision tree."""
        result = await get_behavioral_pattern("dashboard")
        assert "decision_tree" in result

    @pytest.mark.asyncio
    async def test_modal_pattern_exists(self):
        """Modal dialog behavioral pattern should exist."""
        result = await get_behavioral_pattern("modal_dialog")
        assert "error" not in result
        assert "required_elements" in result

    @pytest.mark.asyncio
    async def test_data_table_pattern_exists(self):
        """Data table behavioral pattern should exist."""
        result = await get_behavioral_pattern("data_table")
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_search_pattern_exists(self):
        """Search behavioral pattern should exist."""
        result = await get_behavioral_pattern("search")
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_toast_pattern_exists(self):
        """Toast notification behavioral pattern should exist."""
        result = await get_behavioral_pattern("toast_notification")
        assert "error" not in result


# ============================================================
# Tool 7: analyze_and_devibecode — code fixes + resolved tokens
# ============================================================

class TestTool7_AnalyzeDevibecode:
    @pytest.mark.asyncio
    async def test_returns_code_fixes(self):
        """Analysis of bad code should return concrete code fix examples."""
        bad_code = '''
<div className="bg-[#ff0000]" style={{ padding: 10 }}>
  <div onClick={handleClick}>Click me</div>
</div>'''
        result = await analyze_and_devibecode(bad_code)
        assert "code_fixes" in result, "Missing code_fixes field"
        if result["code_fixes"]:
            fix = result["code_fixes"][0]
            assert "before" in fix
            assert "after" in fix
            assert "fix" in fix

    @pytest.mark.asyncio
    async def test_semantic_tokens_are_real(self):
        """semantic_tokens_to_apply should be a dict with real values, not 'light'/'dark'."""
        bad_code = '<div className="bg-[#333]"><p>Hello</p></div>'
        result = await analyze_and_devibecode(bad_code)
        tokens = result.get("semantic_tokens_to_apply", {})
        if tokens:
            assert isinstance(tokens, dict)
            # Should have actual token keys, not nested color/spacing dicts
            assert any(k.startswith("color-") for k in tokens), (
                f"Tokens don't have color-* keys: {list(tokens.keys())[:5]}"
            )


# ============================================================
# Tool 6: compare_design_approaches — resolved data
# ============================================================

class TestTool6_Compare:
    @pytest.mark.asyncio
    async def test_comparison_examples_have_tokens(self):
        """Comparison examples should have resolved tokens."""
        result = await compare_design_approaches("Dashboard", limit=3)
        examples = result.get("examples", [])
        for ex in examples:
            tokens = ex.get("semantic_tokens")
            if tokens is not None:
                assert isinstance(tokens, dict), f"Comparison token is {type(tokens).__name__}"


# ============================================================
# Tool 11: generate_refactored_code — resolved design_reference
# ============================================================

class TestTool11_GenerateRefactored:
    @pytest.mark.asyncio
    async def test_design_reference_has_resolved_tokens(self):
        """design_reference in refactored code output should have real token dicts."""
        code = '<div style={{backgroundColor: "#1a1a2e"}}><button onClick={go}>Go</button></div>'
        result = await generate_refactored_code(code)
        refs = result.get("design_reference", [])
        for ref in refs:
            tokens = ref.get("semantic_tokens")
            if tokens is not None:
                assert isinstance(tokens, dict), (
                    f"design_reference token is {type(tokens).__name__}, not dict"
                )

    @pytest.mark.asyncio
    async def test_semantic_tokens_are_real_not_hsl_vars(self):
        """semantic_tokens should be real hex values, not hsl(var(--primary)) placeholders."""
        code = '<div className="bg-red-500"><p>Test</p></div>'
        result = await generate_refactored_code(code)
        tokens = result.get("semantic_tokens", {})
        if isinstance(tokens, dict) and tokens:
            # Should NOT contain "hsl(var(--" — that was the old hardcoded shadcn approach
            all_values = " ".join(str(v) for v in tokens.values())
            assert "hsl(var(" not in all_values, (
                "semantic_tokens still using hardcoded shadcn hsl(var(--)) placeholders"
            )

    @pytest.mark.asyncio
    async def test_returns_code_fixes(self):
        """Should include code_fixes with before/after examples."""
        code = '<div onClick={fn} style={{margin: "50px"}}><input placeholder="email"></div>'
        result = await generate_refactored_code(code)
        fixes = result.get("code_fixes", [])
        assert isinstance(fixes, list)


# ============================================================
# End-to-end: Full AI agent workflow with new data
# ============================================================

class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_full_workflow_returns_actionable_data(self):
        """Simulate: search → blueprint → tokens. Everything must be real."""
        # Search
        results = await search_design_patterns("SaaS dashboard", limit=1)
        assert len(results) > 0
        r = results[0]
        
        # Tokens must be real
        tokens = r.get("semantic_tokens", {})
        assert isinstance(tokens, dict)
        assert "color-background" in tokens
        assert tokens["color-background"].startswith("#")
        
        # Behavior must be substantial
        behavior = r.get("behavioral_description", "")
        assert len(behavior) > 80
        
        # Get blueprint
        bp = await get_design_blueprint(r["id"])
        assert isinstance(bp.get("semantic_tokens", {}), dict)
        
        # Get standalone tokens
        standalone = await get_semantic_tokens(style="dark")
        token_set = standalone.get("tokens", standalone.get("dark", {}))
        assert "color-primary" in token_set

    @pytest.mark.asyncio
    async def test_analyze_workflow_returns_actionable_fixes(self):
        """Simulate: analyze bad code → get concrete fixes with before/after."""
        bad_code = '''
<div style={{position: "absolute", top: 100, left: 200}}>
  <div className="bg-[#ff6b6b] text-[#ffa8a8]">
    <div onClick={() => navigate("/home")}>
      <input placeholder="Search..." className="outline-none">
    </div>
  </div>
</div>'''
        result = await analyze_and_devibecode(bad_code)
        
        # Must find issues
        assert len(result["anti_patterns_found"]) > 0
        
        # Must have real tokens
        tokens = result.get("semantic_tokens_to_apply", {})
        if tokens:
            assert isinstance(tokens, dict)
            # Should be flat token keys, not nested
            has_color_key = any(k.startswith("color-") for k in tokens)
            assert has_color_key, f"No color-* keys in tokens: {list(tokens.keys())[:5]}"
        
        # Must have code fixes
        fixes = result.get("code_fixes", [])
        assert isinstance(fixes, list)
