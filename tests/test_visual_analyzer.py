"""Tests for the visual design analyzer."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.visual_analyzer import (
    hex_to_rgb, relative_luminance, contrast_ratio, rgb_to_hsl,
    color_distance, extract_colors, detect_color_contrast_issues,
    detect_color_palette_issues, detect_spacing_inconsistency,
    detect_typography_issues, detect_visual_hierarchy,
    detect_dark_mode_issues, analyze_visual,
    generate_color_palette, FONT_PAIRINGS, TYPE_SCALE, SPACING_SYSTEM,
)


# ============================================================
# Color Utility Tests
# ============================================================

class TestColorUtilities:
    def test_hex_to_rgb_full(self):
        assert hex_to_rgb('#ff0000') == (255, 0, 0)
        assert hex_to_rgb('#00ff00') == (0, 255, 0)
        assert hex_to_rgb('000000') == (0, 0, 0)
    
    def test_hex_to_rgb_short(self):
        assert hex_to_rgb('#fff') == (255, 255, 255)
        assert hex_to_rgb('#f00') == (255, 0, 0)
    
    def test_relative_luminance(self):
        assert relative_luminance(255, 255, 255) == pytest.approx(1.0, abs=0.01)
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0, abs=0.01)
    
    def test_contrast_ratio_black_white(self):
        ratio = contrast_ratio('#000000', '#ffffff')
        assert ratio == pytest.approx(21.0, abs=0.1)
    
    def test_contrast_ratio_same_color(self):
        ratio = contrast_ratio('#3b82f6', '#3b82f6')
        assert ratio == pytest.approx(1.0, abs=0.01)
    
    def test_contrast_ratio_symmetry(self):
        r1 = contrast_ratio('#3b82f6', '#ffffff')
        r2 = contrast_ratio('#ffffff', '#3b82f6')
        assert r1 == pytest.approx(r2, abs=0.01)
    
    def test_rgb_to_hsl(self):
        h, s, l = rgb_to_hsl(255, 0, 0)
        assert h == pytest.approx(0, abs=1)
        assert s == pytest.approx(100, abs=1)
        assert l == pytest.approx(50, abs=1)
    
    def test_color_distance_same(self):
        assert color_distance('#ff0000', '#ff0000') == 0
    
    def test_color_distance_different(self):
        dist = color_distance('#ff0000', '#0000ff')
        assert dist > 300  # Very different


# ============================================================
# Extract Colors Tests
# ============================================================

class TestExtractColors:
    def test_extract_hex_colors(self):
        code = 'color: #ff5733; background: #2ecc71;'
        colors = extract_colors(code)
        hexes = [c['hex'] for c in colors]
        assert '#ff5733' in hexes
        assert '#2ecc71' in hexes
    
    def test_extract_tailwind_colors(self):
        code = 'className="bg-blue-500 text-white"'
        colors = extract_colors(code)
        assert len(colors) >= 1  # At least blue
    
    def test_extract_short_hex(self):
        code = 'color: #f00;'
        colors = extract_colors(code)
        assert any(c['hex'] == '#ff0000' for c in colors)


# ============================================================
# Detector Tests
# ============================================================

class TestColorContrastDetector:
    def test_good_contrast(self):
        code = 'className="bg-white text-black"'
        findings = detect_color_contrast_issues(code)
        assert len(findings) == 0  # Should pass
    
    def test_bad_contrast_muted_on_dark(self):
        code = 'className="bg-slate-900 text-slate-500"'
        findings = detect_color_contrast_issues(code)
        assert len(findings) > 0
        assert any(f['type'] == 'low_contrast' for f in findings)


class TestColorPaletteDetector:
    def test_few_colors_ok(self):
        code = 'bg-blue-500 text-white border-gray-200'
        findings = detect_color_palette_issues(code)
        proliferation = [f for f in findings if f['type'] == 'color_proliferation']
        assert len(proliferation) == 0
    
    def test_too_many_colors(self):
        # 10+ distinct chromatic colors
        code = '''
            bg-red-500 bg-blue-500 bg-green-500 bg-yellow-500 bg-purple-500
            bg-pink-500 bg-orange-500 bg-teal-500 bg-indigo-500 bg-cyan-500
        '''
        findings = detect_color_palette_issues(code)
        proliferation = [f for f in findings if f['type'] == 'color_proliferation']
        assert len(proliferation) > 0


class TestSpacingDetector:
    def test_consistent_spacing(self):
        code = 'p-4 m-2 gap-4 p-8 m-4'
        findings = detect_spacing_inconsistency(code)
        # Should be fine — using standard scale values
        consistency = [f for f in findings if f['type'] == 'spacing_inconsistency']
        assert len(consistency) == 0
    
    def test_too_many_values(self):
        code = 'p-1 p-2 p-3 p-4 p-5 p-6 p-7 p-8 p-9 p-10 p-11 p-12 p-14'
        findings = detect_spacing_inconsistency(code)
        consistency = [f for f in findings if f['type'] == 'spacing_inconsistency']
        assert len(consistency) > 0


class TestTypographyDetector:
    def test_good_typography(self):
        code = 'text-sm text-base text-lg text-xl font-normal font-bold'
        findings = detect_typography_issues(code)
        scale = [f for f in findings if f['type'] == 'typography_scale']
        assert len(scale) == 0
    
    def test_too_many_sizes(self):
        code = 'text-xs text-sm text-base text-lg text-xl text-2xl text-3xl text-4xl'
        findings = detect_typography_issues(code)
        scale = [f for f in findings if f['type'] == 'typography_scale']
        assert len(scale) > 0
    
    def test_excessive_xs(self):
        code = 'text-xs text-xs text-xs text-xs text-xs text-xs text-xs text-xs text-sm text-base'
        findings = detect_typography_issues(code)
        small = [f for f in findings if f['type'] == 'text_too_small']
        assert len(small) > 0


class TestVisualHierarchyDetector:
    def test_proper_hierarchy(self):
        code = '<h1 className="text-3xl">Title</h1><h2 className="text-xl">Sub</h2>'
        findings = detect_visual_hierarchy(code)
        assert len(findings) == 0
    
    def test_broken_hierarchy(self):
        code = '<h1 className="text-sm">Title</h1><h2 className="text-xl">Sub</h2>'
        findings = detect_visual_hierarchy(code)
        assert any(f['type'] == 'heading_hierarchy' for f in findings)


class TestDarkModeDetector:
    def test_has_dark_mode(self):
        code = 'className="bg-white dark:bg-gray-900 text-black dark:text-white"'
        findings = detect_dark_mode_issues(code)
        missing = [f for f in findings if f['type'] == 'missing_dark_mode']
        assert len(missing) == 0
    
    def test_missing_dark_mode(self):
        code = 'className="bg-white text-black"'
        findings = detect_dark_mode_issues(code)
        missing = [f for f in findings if f['type'] == 'missing_dark_mode']
        assert len(missing) > 0


# ============================================================
# Color Palette Generator Tests
# ============================================================

class TestColorPaletteGenerator:
    def test_generates_shades(self):
        palette = generate_color_palette('#3b82f6')
        assert 'primary' in palette
        assert 'shades' in palette['primary']
        assert len(palette['primary']['shades']) == 11  # 50 through 950
    
    def test_generates_themes(self):
        palette = generate_color_palette('#3b82f6', mode='both')
        assert 'light_theme' in palette
        assert 'dark_theme' in palette
    
    def test_generates_css_variables(self):
        palette = generate_color_palette('#3b82f6')
        assert 'css_variables' in palette
        assert 'light' in palette['css_variables']
        assert 'dark' in palette['css_variables']
    
    def test_generates_accent(self):
        palette = generate_color_palette('#3b82f6')
        assert 'accent' in palette
        assert palette['accent']['hex'].startswith('#')
    
    def test_generates_semantic(self):
        palette = generate_color_palette('#3b82f6')
        assert 'semantic' in palette
        assert 'success' in palette['semantic']
        assert 'error' in palette['semantic']


# ============================================================
# Reference Data Tests
# ============================================================

class TestReferenceData:
    def test_font_pairings_exist(self):
        assert len(FONT_PAIRINGS) >= 5
        for name, pairing in FONT_PAIRINGS.items():
            assert 'heading' in pairing
            assert 'body' in pairing
            assert 'mono' in pairing
            assert 'description' in pairing
    
    def test_type_scales_exist(self):
        assert len(TYPE_SCALE) >= 2
        for name, scale in TYPE_SCALE.items():
            assert 'sizes' in scale
            assert 'body' in scale['sizes']
            assert 'heading_1' in scale['sizes']
    
    def test_spacing_systems_exist(self):
        assert len(SPACING_SYSTEM) >= 3
        for name, system in SPACING_SYSTEM.items():
            assert 'scale' in system
            assert 'md' in system['scale']


# ============================================================
# Integration: analyze_visual
# ============================================================

class TestAnalyzeVisual:
    def test_returns_structure(self):
        result = analyze_visual('className="bg-white text-black p-4"')
        assert 'findings' in result
        assert 'severity_summary' in result
        assert 'colors_found' in result
    
    def test_empty_code(self):
        result = analyze_visual('')
        assert result['findings'] == []
    
    def test_finds_issues(self):
        code = '''
        <div className="bg-slate-900 text-slate-500 p-1 p-2 p-3 p-4 p-5 p-6 p-7 p-8 p-9 p-10 p-11 p-12 p-14">
            <h1 className="text-sm font-normal">Title</h1>
            <h2 className="text-xl font-normal">Subtitle</h2>
        </div>
        '''
        result = analyze_visual(code)
        assert len(result['findings']) > 0
