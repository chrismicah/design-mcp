"""
Tests for visual recipes — the design craft layer that prevents vibecoded output.
V2: Updated for restrained recipes based on real site analysis.
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
    """Every recipe must have actionable guidance with anti-patterns."""

    REQUIRED_RECIPES = [
        "color_restraint", "depth_system", "typography_is_design",
        "whitespace_as_design", "component_design", "motion_restraint",
        "surface_treatment", "layout_hierarchy",
    ]

    def test_all_required_recipes_exist(self, recipes):
        for name in self.REQUIRED_RECIPES:
            assert name in recipes, f"Missing required recipe: {name}"

    def test_color_restraint_has_palettes(self, recipes):
        r = recipes["color_restraint"]
        assert "palettes" in r, "color_restraint missing palettes"
        assert "rules" in r, "color_restraint missing rules"
        # Must have real-world reference palettes
        palettes = r["palettes"]
        assert len(palettes) >= 3, f"Only {len(palettes)} palettes — need real-world examples"
        # Each palette must have bg, fg, accent, border
        for name, pal in palettes.items():
            assert "bg" in pal, f"Palette '{name}' missing bg"
            assert "fg" in pal, f"Palette '{name}' missing fg"
            assert "accent" in pal, f"Palette '{name}' missing accent"

    def test_color_restraint_has_anti_patterns(self, recipes):
        r = recipes["color_restraint"]
        assert "anti_patterns" in r
        ap_text = " ".join(r["anti_patterns"]).lower()
        assert "glass" in ap_text or "gradient" in ap_text, "Must warn against glass/gradients"

    def test_depth_system_has_dark_and_light(self, recipes):
        r = recipes["depth_system"]
        assert "dark" in r, "depth_system missing dark variant"
        assert "light" in r, "depth_system missing light variant"
        # Dark must have actual hex values
        dark = r["dark"]
        assert "base" in dark
        assert "surface" in dark
        assert dark["base"].startswith("#")

    def test_typography_has_system(self, recipes):
        r = recipes["typography_is_design"]
        assert "system" in r, "typography missing type system"
        system = r["system"]
        assert len(system) >= 4, f"Only {len(system)} type tiers — need at least 4"
        assert "rules" in r

    def test_whitespace_has_rules(self, recipes):
        r = recipes["whitespace_as_design"]
        assert "rules" in r
        assert len(r["rules"]) >= 5
        assert "anti_patterns" in r

    def test_component_design_has_stat_card(self, recipes):
        r = recipes["component_design"]
        assert "stat_card" in r, "component_design missing stat_card"
        card = r["stat_card"]
        assert "anti_patterns" in card, "stat_card missing anti-patterns"

    def test_component_design_has_sidebar(self, recipes):
        r = recipes["component_design"]
        assert "sidebar" in r
        assert "anti_patterns" in r["sidebar"]

    def test_component_design_has_data_table(self, recipes):
        r = recipes["component_design"]
        assert "data_table" in r
        assert "anti_patterns" in r["data_table"]

    def test_component_design_has_chart(self, recipes):
        r = recipes["component_design"]
        assert "chart" in r
        assert "anti_patterns" in r["chart"]

    def test_motion_restraint_has_rules(self, recipes):
        r = recipes["motion_restraint"]
        assert "rules" in r
        assert "anti_patterns" in r

    def test_surface_treatment_has_techniques(self, recipes):
        r = recipes["surface_treatment"]
        assert "techniques" in r
        assert "anti_patterns" in r

    def test_layout_hierarchy_has_rules(self, recipes):
        r = recipes["layout_hierarchy"]
        assert "rules" in r
        assert "anti_patterns" in r


class TestRecipeIntegration:
    """Recipes must be wired into tool responses."""

    @pytest.mark.asyncio
    async def test_get_visual_recipe_returns_all(self):
        from server import get_visual_recipe
        result = await get_visual_recipe()
        assert "color_restraint" in result
        assert "depth_system" in result
        assert "typography_is_design" in result

    @pytest.mark.asyncio
    async def test_get_visual_recipe_by_name(self):
        from server import get_visual_recipe
        result = await get_visual_recipe(recipe="color_restraint")
        assert "palettes" in result
        assert "rules" in result

    @pytest.mark.asyncio
    async def test_get_visual_recipe_by_page_type(self):
        from server import get_visual_recipe
        result = await get_visual_recipe(page_type="Dashboard")
        assert "color_restraint" in result
        assert "component_design" in result
        assert "typography_is_design" in result

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
        assert "typography_is_design" in vr or "component_design" in vr

    @pytest.mark.asyncio
    async def test_generate_refactored_includes_visual_recipes(self):
        from server import generate_refactored_code
        code = '<div style="background: red"><button>Click</button></div>'
        result = await generate_refactored_code(code)
        assert "visual_recipes" in result, "generate_refactored_code missing visual_recipes"


class TestAntiVibecodeSignals:
    """Ensure the MCP actively prevents common AI-generated patterns."""

    def test_bans_glass_effects(self, recipes):
        """Glass/blur must be listed as anti-patterns."""
        all_anti = []
        for key, recipe in recipes.items():
            if isinstance(recipe, dict):
                ap = recipe.get("anti_patterns", [])
                if isinstance(ap, list):
                    all_anti.extend(ap)
                # Check nested anti-patterns (component_design has sub-components)
                for v in recipe.values():
                    if isinstance(v, dict) and "anti_patterns" in v:
                        all_anti.extend(v["anti_patterns"])
        all_text = " ".join(all_anti).lower()
        assert "glass" in all_text or "blur" in all_text, "Must ban glass/blur effects"

    def test_bans_gradient_backgrounds(self, recipes):
        """Gradient backgrounds must be listed as anti-patterns."""
        all_anti = []
        for key, recipe in recipes.items():
            if isinstance(recipe, dict):
                for v in recipe.values():
                    if isinstance(v, list):
                        all_anti.extend(str(x) for x in v)
                    elif isinstance(v, dict) and "anti_patterns" in v:
                        all_anti.extend(v["anti_patterns"])
        all_text = " ".join(all_anti).lower()
        assert "gradient" in all_text, "Must ban gradient backgrounds"

    def test_bans_stagger_animations_on_dashboards(self, recipes):
        """Stagger animations must be banned for dashboards."""
        motion = recipes.get("motion_restraint", {})
        ap = motion.get("anti_patterns", [])
        ap_text = " ".join(ap).lower()
        assert "stagger" in ap_text, "Must ban stagger animations on dashboards"

    def test_bans_icon_containers(self, recipes):
        """Colored icon containers (AI signature) must be banned."""
        comp = recipes.get("component_design", {})
        card = comp.get("stat_card", {})
        ap = card.get("anti_patterns", [])
        ap_text = " ".join(ap).lower()
        assert "icon" in ap_text and "container" in ap_text or "circle" in ap_text, (
            "Must ban colored icon containers on stat cards"
        )

    def test_bans_uniform_spacing(self, recipes):
        """Uniform padding everywhere must be banned."""
        ws = recipes.get("whitespace_as_design", {})
        ap = ws.get("anti_patterns", [])
        ap_text = " ".join(ap).lower()
        assert "touch" in ap_text or "crammed" in ap_text or "press" in ap_text, (
            "Must ban tight/uniform spacing"
        )

    def test_has_real_world_palette_references(self, recipes):
        """Must reference real companies (Stripe, Vercel, etc.) not abstract theory."""
        cr = recipes.get("color_restraint", {})
        desc = cr.get("description", "").lower()
        assert "stripe" in desc or "vercel" in desc or "mercury" in desc, (
            "Color restraint must reference real-world sites"
        )
