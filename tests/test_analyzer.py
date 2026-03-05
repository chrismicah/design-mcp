"""Tests for the static analysis anti-pattern detector."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.analyzer import (
    analyze_code,
    infer_component_type,
    detect_magic_hex_colors,
    detect_hardcoded_pixels,
    detect_inline_styles,
    detect_zindex_abuse,
    detect_arbitrary_values,
    detect_margin_alignment,
    detect_absolute_positioning,
    detect_fixed_heights,
    detect_missing_flex_grid,
    detect_redundant_wrappers,
    detect_div_soup,
    detect_interactive_divs,
    detect_missing_aria,
    detect_missing_focus_states,
    detect_unlabeled_inputs,
)


# ============================================================
# STYLING DETECTOR TESTS
# ============================================================

class TestMagicHexColors:
    def test_detects_tailwind_bg_hex(self):
        code = '<div className="bg-[#FF5733] p-4">'
        results = detect_magic_hex_colors(code)
        assert len(results) >= 1
        assert results[0]["type"] == "magic_hex_color"
        assert "#FF5733" in results[0]["message"]

    def test_detects_tailwind_text_hex(self):
        code = '<span className="text-[#0F172A]">Hello</span>'
        results = detect_magic_hex_colors(code)
        assert len(results) >= 1

    def test_detects_inline_style_hex(self):
        code = "style={{ color: '#DC2626' }}"
        results = detect_magic_hex_colors(code)
        assert len(results) >= 1

    def test_no_false_positive_on_clean_code(self):
        code = '<div className="bg-primary text-foreground p-4">'
        results = detect_magic_hex_colors(code)
        assert len(results) == 0


class TestHardcodedPixels:
    def test_detects_width_px(self):
        code = '<div className="w-[400px]">'
        results = detect_hardcoded_pixels(code)
        assert len(results) >= 1
        assert "400px" in results[0]["message"]

    def test_detects_height_px(self):
        code = '<div className="h-[150px]">'
        results = detect_hardcoded_pixels(code)
        assert len(results) >= 1

    def test_detects_padding_px(self):
        code = '<div className="p-[20px]">'
        results = detect_hardcoded_pixels(code)
        assert len(results) >= 1

    def test_ignores_small_border_values(self):
        code = '<div className="border-[1px]">'
        results = detect_hardcoded_pixels(code)
        assert len(results) == 0

    def test_no_false_positive_on_tailwind_scale(self):
        code = '<div className="w-64 h-32 p-4">'
        results = detect_hardcoded_pixels(code)
        assert len(results) == 0


class TestInlineStyles:
    def test_detects_react_inline_style(self):
        code = "<div style={{ padding: '10px', color: 'red' }}>"
        results = detect_inline_styles(code)
        assert len(results) >= 1
        assert results[0]["type"] == "inline_style_abuse"

    def test_detects_html_inline_style(self):
        code = '<div style="padding: 10px; color: red">'
        results = detect_inline_styles(code)
        assert len(results) >= 1

    def test_no_false_positive(self):
        code = '<div className="p-4 text-red-500">'
        results = detect_inline_styles(code)
        assert len(results) == 0


class TestZindexAbuse:
    def test_detects_high_zindex(self):
        code = '<div className="z-[9999]">'
        results = detect_zindex_abuse(code)
        assert len(results) >= 1

    def test_detects_z50(self):
        code = '<div className="z-50">'
        results = detect_zindex_abuse(code)
        assert len(results) >= 1

    def test_ignores_low_zindex(self):
        code = '<div className="z-10">'
        results = detect_zindex_abuse(code)
        assert len(results) == 0


class TestArbitraryValues:
    def test_detects_arbitrary_px(self):
        code = '<div className="p-[13px]">'
        results = detect_arbitrary_values(code)
        assert len(results) >= 1

    def test_detects_arbitrary_rem(self):
        code = '<div className="gap-[1.3rem]">'
        results = detect_arbitrary_values(code)
        assert len(results) >= 1


# ============================================================
# LAYOUT DETECTOR TESTS
# ============================================================

class TestMarginAlignment:
    def test_detects_large_margin_hack(self):
        code = '<div className="ml-[200px]">'
        results = detect_margin_alignment(code)
        assert len(results) >= 1
        assert results[0]["type"] == "margin_alignment_hack"

    def test_detects_large_tailwind_margin(self):
        code = '<div className="ml-64">'
        results = detect_margin_alignment(code)
        assert len(results) >= 1


class TestAbsolutePositioning:
    def test_detects_absolute_with_coords(self):
        code = '<div className="absolute top-[20px] left-[20px]">'
        results = detect_absolute_positioning(code)
        assert len(results) >= 1

    def test_no_false_positive_on_relative(self):
        code = '<div className="relative overflow-hidden">'
        results = detect_absolute_positioning(code)
        assert len(results) == 0


class TestFixedHeights:
    def test_detects_100vh(self):
        code = '<div className="h-[100vh]">'
        results = detect_fixed_heights(code)
        assert len(results) >= 1

    def test_no_false_positive(self):
        code = '<div className="min-h-screen">'
        results = detect_fixed_heights(code)
        assert len(results) == 0


# ============================================================
# STRUCTURAL / A11Y DETECTOR TESTS
# ============================================================

class TestDivSoup:
    def test_detects_deep_nesting(self):
        code = """
        <div><div><div><div><div><div>
            deep content
        </div></div></div></div></div></div>
        """
        results = detect_div_soup(code)
        assert any(f["type"] == "div_soup" for f in results)

    def test_no_false_positive_with_semantic(self):
        code = """
        <main>
            <section>
                <article>
                    <div className="card">content</div>
                </article>
            </section>
        </main>
        """
        results = detect_div_soup(code)
        depth_errors = [f for f in results if "Deep div nesting" in f["message"]]
        assert len(depth_errors) == 0


class TestInteractiveDivs:
    def test_detects_clickable_div(self):
        code = '<div onClick={handleClick} className="cursor-pointer">Click me</div>'
        results = detect_interactive_divs(code)
        assert len(results) >= 1
        assert results[0]["type"] == "interactive_div"
        assert results[0]["severity"] == "error"

    def test_allows_div_with_role_button(self):
        code = '<div onClick={handleClick} role="button" tabIndex={0}>Click me</div>'
        results = detect_interactive_divs(code)
        assert len(results) == 0

    def test_detects_clickable_span(self):
        code = '<span onClick={() => doSomething()}>Action</span>'
        results = detect_interactive_divs(code)
        assert len(results) >= 1


class TestMissingAria:
    def test_detects_toggle_without_aria_expanded(self):
        code = """
        const [open, setOpen] = useState(false);
        <div onClick={() => setOpen(!open)}>Toggle</div>
        """
        results = detect_missing_aria(code)
        assert any(f["type"] == "missing_aria" for f in results)

    def test_no_false_positive_with_aria(self):
        code = """
        const [open, setOpen] = useState(false);
        <div onClick={() => setOpen(!open)} aria-expanded={open}>Toggle</div>
        """
        results = detect_missing_aria(code)
        toggle_findings = [f for f in results if "aria-expanded" in f["message"]]
        assert len(toggle_findings) == 0


class TestMissingFocusStates:
    def test_detects_outline_none_without_focus_ring(self):
        code = '<button className="outline-none bg-blue-500">'
        results = detect_missing_focus_states(code)
        assert len(results) >= 1
        assert results[0]["severity"] == "error"

    def test_allows_outline_none_with_focus_ring(self):
        code = '<button className="outline-none focus:ring-2 focus:ring-blue-500">'
        results = detect_missing_focus_states(code)
        assert len(results) == 0


class TestUnlabeledInputs:
    def test_detects_input_without_label(self):
        code = '<input type="text" placeholder="Enter name" />'
        results = detect_unlabeled_inputs(code)
        assert len(results) >= 1
        assert results[0]["type"] == "unlabeled_input"

    def test_allows_input_with_aria_label(self):
        code = '<input type="text" aria-label="Your name" />'
        results = detect_unlabeled_inputs(code)
        assert len(results) == 0

    def test_allows_hidden_input(self):
        code = '<input type="hidden" name="csrf" value="abc" />'
        results = detect_unlabeled_inputs(code)
        assert len(results) == 0

    def test_allows_input_with_label(self):
        code = """
        <label htmlFor="name">Name</label>
        <input id="name" type="text" />
        """
        results = detect_unlabeled_inputs(code)
        assert len(results) == 0


# ============================================================
# COMPONENT TYPE INFERENCE TESTS
# ============================================================

class TestComponentInference:
    def test_infers_button(self):
        code = "function SubmitButton() { return <button>Submit</button> }"
        assert infer_component_type(code) == "Button"

    def test_infers_dropdown(self):
        code = "function VibeDropdown({ options }) { return <div>dropdown</div> }"
        assert infer_component_type(code) == "Dropdown"

    def test_infers_card(self):
        code = "function UserCard({ name }) { return <div>{name}</div> }"
        assert infer_component_type(code) == "Card"

    def test_infers_nav(self):
        code = "function Navbar() { return <nav>Menu</nav> }"
        assert infer_component_type(code) == "Navigation Bar"

    def test_infers_form(self):
        code = "function LoginForm() { return <form><input /><input /></form> }"
        assert infer_component_type(code) == "Form"

    def test_fallback_to_component(self):
        code = "const x = 42;"
        assert infer_component_type(code) == "Component"


# ============================================================
# FULL ANALYSIS TESTS
# ============================================================

class TestFullAnalysis:
    def test_empty_code(self):
        result = analyze_code("")
        assert result["findings"] == []
        assert result["component_type"] == "Unknown"
        assert result["severity_summary"] == {"errors": 0, "warnings": 0, "info": 0}

    def test_clean_code_minimal_findings(self):
        code = """
        import { Button } from "@/components/ui/button";
        export default function SubmitButton({ onSubmit }) {
            return (
                <Button onClick={onSubmit} variant="default" className="w-full">
                    Submit
                </Button>
            );
        }
        """
        result = analyze_code(code)
        # Clean code should have few or no error findings
        errors = [f for f in result["findings"] if f["severity"] == "error"]
        assert len(errors) == 0

    def test_vibecoded_button_catches_issues(self):
        code = """
        export default function SubmitButton({ onSubmit }) {
            return (
                <div 
                    className="bg-[#2E90FA] text-[#FFFFFF] w-[150px] h-[45px] rounded-[8px] flex items-center justify-center cursor-pointer outline-none"
                    onClick={onSubmit}
                    style={{ boxShadow: '0px 4px 6px rgba(0,0,0,0.1)' }}
                >
                    Submit Data
                </div>
            );
        }
        """
        result = analyze_code(code)
        types = {f["type"] for f in result["findings"]}
        
        assert "magic_hex_color" in types
        assert "hardcoded_pixels" in types
        assert "inline_style_abuse" in types
        assert "interactive_div" in types
        assert result["component_type"] == "Button"

    def test_vibecoded_dropdown_catches_issues(self):
        code = """
        import { useState } from 'react';
        export default function VibeDropdown({ options }) {
            const [open, setOpen] = useState(false);
            return (
                <div className="relative w-[250px]">
                    <div onClick={() => setOpen(!open)} className="border-[#ccc] border-[1px] p-[10px] cursor-pointer">
                        Select
                    </div>
                    {open && (
                        <div className="absolute top-[50px] left-0 bg-white z-[9999] w-[250px]">
                            <div onClick={() => {}} className="p-[10px] hover:bg-[#EFF8FF] cursor-pointer">Option</div>
                        </div>
                    )}
                </div>
            );
        }
        """
        result = analyze_code(code)
        types = {f["type"] for f in result["findings"]}
        
        assert "magic_hex_color" in types
        assert "hardcoded_pixels" in types
        assert "zindex_abuse" in types
        assert "interactive_div" in types
        assert "missing_aria" in types
        assert result["component_type"] == "Dropdown"

    def test_vibecoded_card_catches_issues(self):
        code = """
        export default function UserCard({ name, role }) {
            return (
                <div className="w-[400px] h-[150px] bg-[#FFFFFF] rounded-xl relative overflow-hidden">
                    <div className="absolute top-[20px] left-[20px] bg-[#E2E8F0] w-[50px] h-[50px] rounded-[25px]"></div>
                    <div className="ml-[90px] mt-[25px]">
                        <span className="text-[18px] text-[#0F172A]">{name}</span>
                        <span className="text-[14px] text-[#64748B]">{role}</span>
                    </div>
                    <div className="absolute top-[20px] right-[20px] cursor-pointer" onClick={() => alert('Delete')}>
                        Delete
                    </div>
                </div>
            );
        }
        """
        result = analyze_code(code)
        types = {f["type"] for f in result["findings"]}
        
        assert "magic_hex_color" in types
        assert "hardcoded_pixels" in types
        assert "absolute_positioning" in types
        assert "margin_alignment_hack" in types
        assert "interactive_div" in types
        assert result["component_type"] == "Card"

    def test_severity_summary_counts(self):
        code = """
        <div onClick={fn} className="bg-[#FF0000] outline-none">
            <input type="text" />
        </div>
        """
        result = analyze_code(code)
        summary = result["severity_summary"]
        assert summary["errors"] > 0  # interactive div + missing focus + unlabeled input
        assert isinstance(summary["warnings"], int)
        assert isinstance(summary["info"], int)

    def test_non_ui_code(self):
        code = """
        def calculate_total(items):
            return sum(item.price for item in items)
        """
        result = analyze_code(code)
        assert len(result["findings"]) == 0
