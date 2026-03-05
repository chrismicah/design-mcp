"""Tests for library recommendation tools."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import get_library_recommendations, get_library_details


class TestGetLibraryRecommendations:
    @pytest.mark.asyncio
    async def test_by_use_case_dashboard(self):
        result = await get_library_recommendations(use_case="dashboard")
        assert result["total_libraries"] > 0
        names = [r["name"] for r in result["recommendations"]]
        assert any("shadcn" in n.lower() or "recharts" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_by_use_case_landing_page(self):
        result = await get_library_recommendations(use_case="landing_page")
        names = [r["name"] for r in result["recommendations"]]
        assert any("react bits" in n.lower() or "framer" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_by_ui_elements(self):
        result = await get_library_recommendations(ui_elements=["Button", "Modal", "Data Table"])
        assert result["total_libraries"] > 0
        names = [r["name"] for r in result["recommendations"]]
        assert any("shadcn" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_by_visual_style(self):
        result = await get_library_recommendations(visual_style="Glassmorphism")
        names = [r["name"] for r in result["recommendations"]]
        assert any("react bits" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_needs_animation(self):
        result = await get_library_recommendations(needs_animation=True)
        names = [r["name"] for r in result["recommendations"]]
        assert any("framer" in n.lower() or "motion" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_needs_3d(self):
        result = await get_library_recommendations(needs_3d=True)
        names = [r["name"] for r in result["recommendations"]]
        assert any("three" in n.lower() or "fiber" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_needs_charts(self):
        result = await get_library_recommendations(needs_charts=True)
        names = [r["name"] for r in result["recommendations"]]
        assert any("recharts" in n.lower() or "d3" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_no_filters_returns_premium_stack(self):
        result = await get_library_recommendations()
        assert result["total_libraries"] > 0
        assert "premium_stack" in result

    @pytest.mark.asyncio
    async def test_has_install_commands(self):
        result = await get_library_recommendations(use_case="dashboard")
        for rec in result["recommendations"]:
            assert "install" in rec
            assert rec["install"].startswith("npm") or rec["install"].startswith("npx")

    @pytest.mark.asyncio
    async def test_has_code_examples(self):
        result = await get_library_recommendations(use_case="saas_product")
        examples = [r for r in result["recommendations"] if r.get("example")]
        assert len(examples) > 0

    @pytest.mark.asyncio
    async def test_includes_matching_patterns(self):
        result = await get_library_recommendations(use_case="dashboard")
        assert "matching_design_patterns" in result


class TestGetLibraryDetails:
    @pytest.mark.asyncio
    async def test_get_shadcn(self):
        result = await get_library_details("shadcn")
        assert "library" in result
        assert result["library"]["name"] == "shadcn/ui"
        assert "components" in result["library"]
        assert len(result["library"]["components"]) > 20

    @pytest.mark.asyncio
    async def test_get_react_bits(self):
        result = await get_library_details("react-bits")
        assert "library" in result
        assert "React Bits" in result["library"]["name"]
        assert len(result["library"]["components"]) > 80

    @pytest.mark.asyncio
    async def test_get_framer_motion(self):
        result = await get_library_details("framer-motion")
        assert "library" in result
        assert "Framer" in result["library"]["name"]

    @pytest.mark.asyncio
    async def test_get_by_partial_name(self):
        result = await get_library_details("mantine")
        assert "library" in result
        assert "Mantine" in result["library"]["name"]

    @pytest.mark.asyncio
    async def test_pairs_with(self):
        result = await get_library_details("shadcn")
        assert "pairs_with" in result
        assert len(result["pairs_with"]) > 0

    @pytest.mark.asyncio
    async def test_unknown_library(self):
        result = await get_library_details("nonexistent-lib-xyz")
        assert "error" in result
        assert "available" in result

    @pytest.mark.asyncio
    async def test_all_libraries_have_required_fields(self):
        """Verify data integrity of the libraries database."""
        import json
        libs_path = Path(__file__).parent.parent / "data" / "libraries.json"
        with open(libs_path) as f:
            data = json.load(f)
        
        for lib in data["libraries"]:
            assert "id" in lib
            assert "name" in lib
            assert "category" in lib
            assert "description" in lib
            assert "install" in lib
            assert "docs_url" in lib
            assert "when_to_use" in lib


class TestAnalyzeWithLibraries:
    """Test that analyze_and_devibecode includes library recommendations."""
    
    @pytest.mark.asyncio
    async def test_vibecoded_button_recommends_shadcn(self):
        from server import analyze_and_devibecode
        code = """
        export default function SubmitButton({ onSubmit }) {
            return (
                <div onClick={onSubmit} className="bg-[#2E90FA] text-[#FFFFFF] w-[150px] cursor-pointer">
                    Submit
                </div>
            );
        }
        """
        result = await analyze_and_devibecode(code)
        assert "recommended_libraries" in result
        assert result["detected_component_type"] == "Button"
        if result["recommended_libraries"]:
            names = [r["name"] for r in result["recommended_libraries"]]
            assert any("shadcn" in n.lower() for n in names)

    @pytest.mark.asyncio
    async def test_vibecoded_dropdown_recommends_libraries(self):
        from server import analyze_and_devibecode
        code = """
        export default function VibeDropdown({ options }) {
            const [open, setOpen] = useState(false);
            return <div onClick={() => setOpen(!open)}>Select</div>
        }
        """
        result = await analyze_and_devibecode(code)
        assert result["detected_component_type"] == "Dropdown"
        assert len(result["recommended_libraries"]) > 0
