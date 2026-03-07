"""
Tests for visual recipes — the design craft layer that prevents vibecoded output.
"""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture(scope="module")
def recipes():
    with open(DATA_DIR / "visual_recipes.json") as f:
        return json.load(f)


class TestRecipeCompleteness:
    """Every recipe must have actionable CSS/Tailwind code, not just descriptions."""

    REQUIRED_RECIPES = [
        "glass_card", "gradient_accent", "depth_layers", "text_hierarchy",
        "icon_treatment", "motion_system", "spacing_rhythm", "surface_texture",
        "data_visualization", "table_polish", "sidebar_design",
    ]

    def test_all_required_recipes_exist(self, recipes):
        for name in self.REQUIRED_RECIPES:
            assert name in recipes, f"Missing required recipe: {name}"

    def test_glass_card_has_tailwind(self, recipes):
        r = recipes["glass_card"]
        assert "tailwind" in r, "glass_card missing tailwind classes"
        assert "backdrop-blur" in r["tailwind"], "glass_card tailwind should include backdrop-blur"
        assert "hover" in r, "glass_card missing hover treatment"

    def test_depth_layers_has_four_levels(self, recipes):
        r = recipes["depth_layers"]
        assert "levels" in r
        for level in ["base", "raised", "surface", "overlay"]:
            assert level in r["levels"], f"depth_layers missing level: {level}"
            assert "dark" in r["levels"][level], f"depth level '{level}' missing dark variant"
            assert "light" in r["levels"][level], f"depth level '{level}' missing light variant"

    def test_text_hierarchy_has_four_tiers(self, recipes):
        r = recipes["text_hierarchy"]
        assert "tiers" in r
        for tier in ["primary", "secondary", "tertiary", "muted"]:
            assert tier in r["tiers"], f"text_hierarchy missing tier: {tier}"
            assert "dark" in r["tiers"][tier]
            assert "use" in r["tiers"][tier]

    def test_motion_system_has_snippets(self, recipes):
        r = recipes["motion_system"]
        assert "entrance" in r
        assert "micro" in r
        assert "framer_motion_snippet" in r

    def test_icon_treatment_has_rules(self, recipes):
        r = recipes["icon_treatment"]
        assert "rules" in r
        assert len(r["rules"]) >= 3
        # Must mention Lucide/Heroicons
        all_rules = " ".join(r["rules"])
        assert "Lucide" in all_rules or "Heroicons" in all_rules

    def test_spacing_rhythm_has_anti_patterns(self, recipes):
        r = recipes["spacing_rhythm"]
        assert "rules" in r
        assert "anti_patterns" in r
        assert len(r["rules"]) >= 5

    def test_data_viz_has_rules(self, recipes):
        r = recipes["data_visualization"]
        assert "rules" in r
        assert len(r["rules"]) >= 5

    def test_surface_texture_has_noise_css(self, recipes):
        r = recipes["surface_texture"]
        assert "noise_css" in r or "techniques" in r


class TestRecipeIntegration:
    """Recipes must be wired into tool responses."""

    @pytest.mark.asyncio
    async def test_get_visual_recipe_returns_all(self):
        from server import get_visual_recipe
        result = await get_visual_recipe()
        assert "glass_card" in result
        assert "depth_layers" in result
        assert "text_hierarchy" in result

    @pytest.mark.asyncio
    async def test_get_visual_recipe_by_name(self):
        from server import get_visual_recipe
        result = await get_visual_recipe(recipe="glass_card")
        assert "tailwind" in result
        assert "hover" in result

    @pytest.mark.asyncio
    async def test_get_visual_recipe_by_page_type(self):
        from server import get_visual_recipe
        result = await get_visual_recipe(page_type="Dashboard")
        assert "glass_card" in result
        assert "sidebar_design" in result
        assert "table_polish" in result

    @pytest.mark.asyncio
    async def test_blueprint_includes_visual_recipes(self):
        from server import search_design_patterns, get_design_blueprint
        results = await search_design_patterns("dashboard", page_type="Dashboard", limit=1)
        if results:
            bp = await get_design_blueprint(results[0]["id"])
            assert "visual_recipes" in bp, "Blueprint missing visual_recipes"
            vr = bp["visual_recipes"]
            assert isinstance(vr, dict)
            assert len(vr) > 0, "visual_recipes is empty"

    @pytest.mark.asyncio
    async def test_search_results_include_visual_recipes(self):
        from server import search_design_patterns
        results = await search_design_patterns("dashboard", limit=1)
        if results:
            assert "visual_recipes" in results[0], "Search result missing visual_recipes"

    @pytest.mark.asyncio
    async def test_analyze_includes_visual_recipes(self):
        from server import analyze_and_devibecode
        code = '<div style="background: #333; color: #fff; padding: 20px">Hello</div>'
        result = await analyze_and_devibecode(code)
        assert "visual_recipes" in result, "analyze_and_devibecode missing visual_recipes"
        vr = result["visual_recipes"]
        assert "glass_card" in vr or "depth_layers" in vr

    @pytest.mark.asyncio
    async def test_generate_refactored_includes_visual_recipes(self):
        from server import generate_refactored_code
        code = '<div style="background: red"><button>Click</button></div>'
        result = await generate_refactored_code(code)
        assert "visual_recipes" in result, "generate_refactored_code missing visual_recipes"


class TestNoMoreVibecodeSignals:
    """Ensure the MCP actively prevents common vibecoded patterns."""

    def test_icon_treatment_bans_emoji(self, recipes):
        r = recipes["icon_treatment"]
        rules_text = " ".join(r["rules"]).lower()
        assert "emoji" in rules_text, "Icon treatment must explicitly ban emoji"

    def test_depth_layers_enforces_separation(self, recipes):
        r = recipes["depth_layers"]
        assert "rule" in r, "depth_layers needs an explicit rule about layer separation"

    def test_text_hierarchy_enforces_differentiation(self, recipes):
        r = recipes["text_hierarchy"]
        assert "rule" in r, "text_hierarchy needs an explicit rule"

    def test_spacing_bans_uniform_padding(self, recipes):
        r = recipes["spacing_rhythm"]
        ap_text = " ".join(r["anti_patterns"]).lower()
        assert "same" in ap_text or "everywhere" in ap_text, (
            "Spacing anti-patterns must call out uniform padding"
        )
