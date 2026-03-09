"""
Visual design analyzer for detecting color, spacing, and typography issues.

Analyzes source code and CSS/Tailwind for visual design quality:
- Color contrast (WCAG AA/AAA)
- Color palette consistency & harmony  
- Spacing system adherence (8pt grid)
- Typography scale consistency
- Visual hierarchy issues

Uses only Python builtins (re, colorsys, math). No external deps.
"""

import re
import math
import colorsys
from typing import Optional


def finding(type: str, severity: str, message: str,
            line: Optional[int] = None, suggestion: str = "") -> dict:
    return {
        "type": type,
        "severity": severity,
        "message": message,
        "line": line,
        "suggestion": suggestion,
    }


# ============================================================
# COLOR UTILITIES
# ============================================================

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return (0, 0, 0)
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance per WCAG 2.0."""
    def channel(c):
        s = c / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    l1 = relative_luminance(r1, g1, b1)
    l2 = relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB to HSL (h: 0-360, s: 0-100, l: 0-100)."""
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360, s * 100, l * 100)


def color_distance(c1: str, c2: str) -> float:
    """Euclidean distance between two colors in RGB space."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


# ============================================================
# EXTRACT COLORS FROM CODE
# ============================================================

# Tailwind named color classes
TAILWIND_COLORS = {
    'red': '#ef4444', 'orange': '#f97316', 'amber': '#f59e0b',
    'yellow': '#eab308', 'lime': '#84cc16', 'green': '#22c55e',
    'emerald': '#10b981', 'teal': '#14b8a6', 'cyan': '#06b6d4',
    'sky': '#0ea5e9', 'blue': '#3b82f6', 'indigo': '#6366f1',
    'violet': '#8b5cf6', 'purple': '#a855f7', 'fuchsia': '#d946ef',
    'pink': '#ec4899', 'rose': '#f43f5e',
    'slate': '#64748b', 'gray': '#6b7280', 'zinc': '#71717a',
    'neutral': '#737373', 'stone': '#78716c',
    'white': '#ffffff', 'black': '#000000',
}

# Tailwind shade lightness approximations for contrast checking (slate scale)
TAILWIND_SHADE_HEX = {
    'white': '#ffffff', 'black': '#000000',
    '50': '#f8fafc', '100': '#f1f5f9', '200': '#e2e8f0',
    '300': '#cbd5e1', '400': '#94a3b8', '500': '#64748b',
    '600': '#475569', '700': '#334155', '800': '#1e293b',
    '850': '#172033', '900': '#0f172a', '950': '#020617',
}

RE_HEX_COLOR = re.compile(r'#([A-Fa-f0-9]{3,8})\b')
RE_TAILWIND_COLOR = re.compile(
    r'(?:bg|text|border|ring|from|via|to|fill|stroke|decoration|accent|shadow|outline)-'
    r'(red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose|'
    r'slate|gray|zinc|neutral|stone|white|black)(?:-(\d{2,3}))?'
)
RE_HSL_COLOR = re.compile(r'hsl\(\s*([\d.]+)\s*[\s,]\s*([\d.]+)%?\s*[\s,]\s*([\d.]+)%?\s*\)')
RE_CSS_VAR_COLOR = re.compile(r'var\(--([a-zA-Z0-9-]+)\)')


def extract_colors(code: str) -> list[dict]:
    """Extract all color values from code with line numbers."""
    colors = []
    
    for match in RE_HEX_COLOR.finditer(code):
        hex_val = match.group(1)
        if len(hex_val) in (3, 6):
            line = code[:match.start()].count('\n') + 1
            full_hex = hex_val if len(hex_val) == 6 else ''.join(c*2 for c in hex_val)
            colors.append({'hex': f'#{full_hex}', 'line': line, 'source': 'hex'})
    
    for match in RE_TAILWIND_COLOR.finditer(code):
        color_name = match.group(1)
        shade = match.group(2)
        line = code[:match.start()].count('\n') + 1
        hex_val = TAILWIND_COLORS.get(color_name, '#000000')
        colors.append({'hex': hex_val, 'line': line, 'source': 'tailwind', 
                       'name': f'{color_name}-{shade}' if shade else color_name})
    
    return colors


# ============================================================
# VISUAL DETECTORS
# ============================================================

def detect_color_contrast_issues(code: str) -> list[dict]:
    """Detect potential color contrast problems."""
    findings_list = []
    lines = code.split('\n')
    
    # Look for text-color on background patterns within the same element/line
    contrast_pattern = re.compile(
        r'(?:className|class)\s*=\s*["\']([^"\']*)["\']'
    )
    
    for i, line_text in enumerate(lines, 1):
        match = contrast_pattern.search(line_text)
        if not match:
            continue
        classes = match.group(1)
        
        # Extract bg and text colors from the same class string
        bg_match = re.search(r'bg-(white|black|slate|gray|zinc|neutral|stone)(?:-(\d{2,4}))?', classes)
        text_match = re.search(r'text-(white|black|slate|gray|zinc|neutral|stone)(?:-(\d{2,4}))?', classes)
        
        if bg_match and text_match:
            bg_name = bg_match.group(1)
            bg_shade = bg_match.group(2) or ('50' if bg_name == 'white' else '500')
            text_name = text_match.group(1)
            text_shade = text_match.group(2) or ('950' if text_name == 'black' else '500')
            
            bg_hex = TAILWIND_SHADE_HEX.get(bg_shade, TAILWIND_SHADE_HEX.get(bg_name, None))
            text_hex = TAILWIND_SHADE_HEX.get(text_shade, TAILWIND_SHADE_HEX.get(text_name, None))
            if not bg_hex or not text_hex:
                continue  # Unknown shade, skip
            
            ratio = contrast_ratio(bg_hex, text_hex)
            
            if ratio < 3.0:
                findings_list.append(finding(
                    type="low_contrast",
                    severity="error",
                    message=f"Very low contrast ratio ({ratio:.1f}:1) between text-{text_name}-{text_shade} on bg-{bg_name}-{bg_shade}. WCAG AA requires 4.5:1",
                    line=i,
                    suggestion=f"Use text-{text_name}-900/950 on light backgrounds or text-white/100 on dark backgrounds for WCAG AA compliance"
                ))
            elif ratio < 4.5:
                findings_list.append(finding(
                    type="low_contrast",
                    severity="warning",
                    message=f"Contrast ratio ({ratio:.1f}:1) below WCAG AA (4.5:1) for text-{text_name}-{text_shade} on bg-{bg_name}-{bg_shade}",
                    line=i,
                    suggestion="Increase contrast by using a darker text color or lighter background"
                ))
        
        # Check for text colors on dark backgrounds that might be too dim
        if re.search(r'bg-(?:slate|gray|zinc|neutral|stone)-(?:8\d\d|9\d\d|950)', classes):
            if re.search(r'text-(?:slate|gray|zinc|neutral|stone)-(?:4\d\d|5\d\d)', classes):
                findings_list.append(finding(
                    type="low_contrast",
                    severity="warning",
                    message="Muted text on dark background may have insufficient contrast",
                    line=i,
                    suggestion="On dark backgrounds (800+), use text-*-300 or lighter for body text, text-*-400 minimum for secondary text"
                ))
    
    return findings_list


def detect_color_palette_issues(code: str) -> list[dict]:
    """Detect color palette inconsistencies and too many unique colors."""
    findings_list = []
    
    colors = extract_colors(code)
    if len(colors) < 2:
        return findings_list
    
    # Count unique hex colors (normalize to 6-char)
    unique_colors = set()
    for c in colors:
        unique_colors.add(c['hex'].lower())
    
    # Remove common greys/black/white
    neutral_colors = set()
    chromatic_colors = set()
    for hex_val in unique_colors:
        r, g, b = hex_to_rgb(hex_val)
        h, s, l = rgb_to_hsl(r, g, b)
        if s < 10 or l < 5 or l > 95:
            neutral_colors.add(hex_val)
        else:
            chromatic_colors.add(hex_val)
    
    # Too many distinct chromatic colors = no cohesive palette
    if len(chromatic_colors) > 8:
        findings_list.append(finding(
            type="color_proliferation",
            severity="warning",
            message=f"Found {len(chromatic_colors)} distinct chromatic colors — palette lacks cohesion",
            line=None,
            suggestion="Limit to 1-2 primary colors + 1-2 accent colors with systematic shade scales (50-950). Use CSS variables or Tailwind theme colors for consistency."
        ))
    
    # Check for near-duplicate colors (too close to distinguish, wastes palette)
    color_list = list(chromatic_colors)
    near_dupes = []
    for i in range(len(color_list)):
        for j in range(i + 1, len(color_list)):
            dist = color_distance(color_list[i], color_list[j])
            if 5 < dist < 30:  # Very close but not identical
                near_dupes.append((color_list[i], color_list[j]))
    
    if len(near_dupes) > 2:
        findings_list.append(finding(
            type="near_duplicate_colors",
            severity="info",
            message=f"Found {len(near_dupes)} pairs of nearly identical colors — consolidate to a single shade",
            line=None,
            suggestion="Pick one shade per color and use it consistently. Define colors in your Tailwind config or CSS variables."
        ))
    
    return findings_list


def detect_spacing_inconsistency(code: str) -> list[dict]:
    """Detect spacing values that don't follow an 8pt grid or consistent scale."""
    findings_list = []
    
    # Extract all Tailwind spacing values used
    spacing_pattern = re.compile(
        r'(?:p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-[xy])-(\d+(?:\.\d+)?)\b'
    )
    
    spacing_values = []
    for match in spacing_pattern.finditer(code):
        val = float(match.group(1))
        spacing_values.append(val)
    
    if len(spacing_values) < 3:
        return findings_list
    
    # Tailwind standard scale (in spacing units, 1 = 0.25rem = 4px)
    # 8pt grid maps to: 0, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24
    standard_scale = {0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 72, 80, 96}
    
    unique_values = sorted(set(spacing_values))
    off_scale = [v for v in unique_values if v not in standard_scale and v > 0]
    
    # Check how many distinct spacing values are used
    if len(unique_values) > 12:
        findings_list.append(finding(
            type="spacing_inconsistency",
            severity="warning",
            message=f"Using {len(unique_values)} distinct spacing values — too many for visual consistency",
            line=None,
            suggestion=f"Limit to 6-8 spacing values from the Tailwind scale. Used: {', '.join(str(v) for v in unique_values[:10])}{'...' if len(unique_values) > 10 else ''}"
        ))
    
    # Check for non-standard spacing jumps (e.g., going from p-2 to p-7 to p-3)
    # This indicates no consistent spacing rhythm
    if len(off_scale) > 3:
        findings_list.append(finding(
            type="spacing_off_scale",
            severity="info",
            message=f"Found {len(off_scale)} spacing values off the standard Tailwind scale",
            line=None,
            suggestion=f"Map non-standard values to nearest scale: {', '.join(str(v) for v in off_scale[:5])}"
        ))
    
    return findings_list


def detect_typography_issues(code: str) -> list[dict]:
    """Detect typography problems: inconsistent sizing, missing hierarchy, poor font usage."""
    findings_list = []
    
    # Extract text size classes
    text_size_pattern = re.compile(r'text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)\b')
    font_weight_pattern = re.compile(r'font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)\b')
    leading_pattern = re.compile(r'leading-(\w+)\b')
    tracking_pattern = re.compile(r'tracking-(\w+)\b')
    
    text_sizes = [m.group(1) for m in text_size_pattern.finditer(code)]
    font_weights = [m.group(1) for m in font_weight_pattern.finditer(code)]
    leadings = [m.group(1) for m in leading_pattern.finditer(code)]
    
    SIZE_ORDER = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl']
    
    if text_sizes:
        unique_sizes = sorted(set(text_sizes), key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 0)
        
        # Too many different text sizes = no type hierarchy
        if len(unique_sizes) > 6:
            findings_list.append(finding(
                type="typography_scale",
                severity="warning",
                message=f"Using {len(unique_sizes)} distinct text sizes — define a clear type scale",
                line=None,
                suggestion="Limit to 4-6 sizes: xs (caption), sm (body small), base (body), lg (subhead), xl-2xl (heading), 3xl+ (display). Map to semantic names."
            ))
        
        # Check if body text is too small
        if 'xs' in text_sizes:
            xs_count = text_sizes.count('xs')
            total = len(text_sizes)
            if xs_count / total > 0.3:
                findings_list.append(finding(
                    type="text_too_small",
                    severity="warning",
                    message=f"text-xs used extensively ({xs_count}/{total} text elements) — may cause readability issues",
                    line=None,
                    suggestion="text-xs (12px) is too small for body text. Use text-sm (14px) minimum for readable body content."
                ))
    
    # Check for missing line-height on long text
    if len(text_sizes) > 0 and len(leadings) == 0:
        # Check if there are likely paragraphs or long text
        has_paragraphs = bool(re.search(r'<p\b|<article|<section.*\n.*text-', code))
        if has_paragraphs:
            findings_list.append(finding(
                type="missing_line_height",
                severity="info",
                message="No explicit line-height (leading-*) classes found — text may be cramped or too loose",
                line=None,
                suggestion="Add leading-relaxed (1.625) for body text, leading-tight (1.25) for headings. Default leading-normal (1.5) works for most body text."
            ))
    
    # Check for missing font-weight variety (no visual hierarchy)
    if font_weights:
        unique_weights = set(font_weights)
        if len(unique_weights) == 1:
            findings_list.append(finding(
                type="flat_weight_hierarchy",
                severity="info",
                message=f"Only using font-{list(unique_weights)[0]} — no weight variation for visual hierarchy",
                line=None,
                suggestion="Use font-bold/semibold for headings, font-medium for labels, font-normal for body text to create clear visual hierarchy."
            ))
    elif text_sizes and len(text_sizes) > 3:
        findings_list.append(finding(
            type="missing_font_weights",
            severity="info",
            message="No font-weight classes found — text may lack visual hierarchy",
            line=None,
            suggestion="Add font-bold for headings, font-medium for emphasis, font-normal for body text."
        ))
    
    # Detect hardcoded font-family that should be a CSS variable
    font_family_pattern = re.compile(r'font-(?:family|face)\s*:\s*["\']?([^;"\'}\)]+)')
    for match in font_family_pattern.finditer(code):
        font = match.group(1).strip()
        line = code[:match.start()].count('\n') + 1
        if 'var(--' not in font and 'inherit' not in font:
            findings_list.append(finding(
                type="hardcoded_font",
                severity="info",
                message=f"Hardcoded font-family: {font[:50]}",
                line=line,
                suggestion="Define fonts in Tailwind config (fontFamily) or CSS variables for consistency across the project."
            ))
    
    return findings_list


def detect_visual_hierarchy(code: str) -> list[dict]:
    """Detect missing visual hierarchy patterns."""
    findings_list = []
    
    # Check for heading tags with no size differentiation
    heading_pattern = re.compile(r'<h([1-6])\b[^>]*(?:className|class)\s*=\s*["\']([^"\']*)["\']')
    headings = []
    for match in heading_pattern.finditer(code):
        level = int(match.group(1))
        classes = match.group(2)
        size_match = re.search(r'text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)', classes)
        size = size_match.group(1) if size_match else 'base'
        headings.append({'level': level, 'size': size, 'line': code[:match.start()].count('\n') + 1})
    
    if len(headings) >= 2:
        SIZE_ORDER = ['xs', 'sm', 'base', 'lg', 'xl', '2xl', '3xl', '4xl', '5xl', '6xl', '7xl', '8xl', '9xl']
        # Check if heading sizes decrease properly with level
        for i in range(len(headings) - 1):
            h1 = headings[i]
            h2 = headings[i + 1]
            if h1['level'] < h2['level']:  # h1 before h2 = h1 should be bigger
                idx1 = SIZE_ORDER.index(h1['size']) if h1['size'] in SIZE_ORDER else 3
                idx2 = SIZE_ORDER.index(h2['size']) if h2['size'] in SIZE_ORDER else 3
                if idx1 <= idx2:  # Higher-level heading is same size or smaller — bad
                    findings_list.append(finding(
                        type="heading_hierarchy",
                        severity="warning",
                        message=f"h{h1['level']} (text-{h1['size']}) is not larger than h{h2['level']} (text-{h2['size']}) — broken visual hierarchy",
                        line=h2['line'],
                        suggestion=f"h{h1['level']} should be larger than h{h2['level']}. Try text-{SIZE_ORDER[min(idx2+2, len(SIZE_ORDER)-1)]} for h{h1['level']}."
                    ))
    
    return findings_list


def detect_dark_mode_issues(code: str) -> list[dict]:
    """Detect missing or incomplete dark mode support."""
    findings_list = []
    
    has_dark_classes = bool(re.search(r'\bdark:', code))
    has_bg_colors = bool(re.search(r'bg-(?:white|slate|gray|zinc|neutral|stone)', code))
    has_text_colors = bool(re.search(r'text-(?:black|slate|gray|zinc|neutral|stone)-(?:7\d\d|8\d\d|9\d\d|950)', code))
    
    # Has light mode colors but no dark: variants
    if (has_bg_colors or has_text_colors) and not has_dark_classes:
        # Check if using CSS variables (which handle dark mode automatically)
        uses_css_vars = bool(re.search(r'(?:bg|text)-(?:background|foreground|primary|secondary|muted|accent|destructive|card|popover)\b', code))
        if not uses_css_vars:
            findings_list.append(finding(
                type="missing_dark_mode",
                severity="info",
                message="Hardcoded light-mode colors without dark: variants — no dark mode support",
                line=None,
                suggestion="Add dark: variants (dark:bg-gray-900 dark:text-white) or use semantic tokens (bg-background text-foreground) that auto-adapt."
            ))
    
    # Partial dark mode (some elements have dark:, others don't)
    if has_dark_classes:
        dark_count = len(re.findall(r'\bdark:', code))
        bg_count = len(re.findall(r'bg-(?:white|slate|gray|zinc|neutral|stone)', code))
        if bg_count > 0 and dark_count < bg_count * 0.3:
            findings_list.append(finding(
                type="incomplete_dark_mode",
                severity="info",
                message=f"Incomplete dark mode: only {dark_count} dark: variants for {bg_count} background colors",
                line=None,
                suggestion="Ensure all background and text colors have dark: variants, or migrate to CSS variable-based tokens."
            ))
    
    return findings_list


# ============================================================
# VISUAL SUGGESTIONS GENERATOR
# ============================================================

# Curated font pairings by brand personality
FONT_PAIRINGS = {
    "clean_modern": {
        "heading": "Inter",
        "body": "Inter",
        "mono": "JetBrains Mono",
        "description": "Clean, modern, versatile — works for SaaS, dashboards, any professional app",
        "css": "font-family: 'Inter', system-ui, -apple-system, sans-serif;",
        "tailwind": "fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }",
    },
    "editorial": {
        "heading": "Playfair Display",
        "body": "Source Sans 3",
        "mono": "Source Code Pro",
        "description": "Elegant serif + clean sans-serif — editorial, luxury, content-heavy",
        "css": "font-family: 'Playfair Display', Georgia, serif;",
        "tailwind": "fontFamily: { serif: ['Playfair Display', 'Georgia', 'serif'], sans: ['Source Sans 3', 'sans-serif'] }",
    },
    "geometric": {
        "heading": "Space Grotesk",
        "body": "DM Sans",
        "mono": "DM Mono",
        "description": "Geometric, tech-forward — startups, developer tools, crypto",
        "css": "font-family: 'Space Grotesk', sans-serif;",
        "tailwind": "fontFamily: { sans: ['DM Sans', 'sans-serif'], display: ['Space Grotesk', 'sans-serif'] }",
    },
    "friendly": {
        "heading": "Nunito",
        "body": "Nunito Sans",
        "mono": "Fira Code",
        "description": "Rounded, approachable — consumer apps, education, kids",
        "css": "font-family: 'Nunito', sans-serif;",
        "tailwind": "fontFamily: { sans: ['Nunito Sans', 'sans-serif'], display: ['Nunito', 'sans-serif'] }",
    },
    "professional": {
        "heading": "Plus Jakarta Sans",
        "body": "Plus Jakarta Sans",
        "mono": "JetBrains Mono",
        "description": "Professional, modern — enterprise, fintech, legal",
        "css": "font-family: 'Plus Jakarta Sans', sans-serif;",
        "tailwind": "fontFamily: { sans: ['Plus Jakarta Sans', 'sans-serif'] }",
    },
    "brutalist": {
        "heading": "Instrument Serif",
        "body": "IBM Plex Sans",
        "mono": "IBM Plex Mono",
        "description": "Bold serif headers + clean body — portfolio, agency, creative",
        "css": "font-family: 'Instrument Serif', serif;",
        "tailwind": "fontFamily: { serif: ['Instrument Serif', 'serif'], sans: ['IBM Plex Sans', 'sans-serif'] }",
    },
}

# Type scale based on major third (1.250) — most versatile
TYPE_SCALE = {
    "major_third": {
        "name": "Major Third (1.250)",
        "ratio": 1.25,
        "description": "Versatile, works for most UIs. Not too dramatic, not too flat.",
        "sizes": {
            "caption": {"size": "0.75rem", "tailwind": "text-xs", "line_height": "1rem"},
            "body_small": {"size": "0.875rem", "tailwind": "text-sm", "line_height": "1.25rem"},
            "body": {"size": "1rem", "tailwind": "text-base", "line_height": "1.5rem"},
            "subhead": {"size": "1.125rem", "tailwind": "text-lg", "line_height": "1.75rem"},
            "heading_3": {"size": "1.25rem", "tailwind": "text-xl", "line_height": "1.75rem"},
            "heading_2": {"size": "1.5rem", "tailwind": "text-2xl", "line_height": "2rem"},
            "heading_1": {"size": "1.875rem", "tailwind": "text-3xl", "line_height": "2.25rem"},
            "display": {"size": "2.25rem", "tailwind": "text-4xl", "line_height": "2.5rem"},
        },
    },
    "perfect_fourth": {
        "name": "Perfect Fourth (1.333)",
        "ratio": 1.333,
        "description": "More dramatic hierarchy. Great for editorial, marketing, and landing pages.",
        "sizes": {
            "caption": {"size": "0.75rem", "tailwind": "text-xs", "line_height": "1rem"},
            "body_small": {"size": "0.875rem", "tailwind": "text-sm", "line_height": "1.25rem"},
            "body": {"size": "1rem", "tailwind": "text-base", "line_height": "1.5rem"},
            "subhead": {"size": "1.25rem", "tailwind": "text-xl", "line_height": "1.75rem"},
            "heading_3": {"size": "1.5rem", "tailwind": "text-2xl", "line_height": "2rem"},
            "heading_2": {"size": "1.875rem", "tailwind": "text-3xl", "line_height": "2.25rem"},
            "heading_1": {"size": "2.25rem", "tailwind": "text-4xl", "line_height": "2.5rem"},
            "display": {"size": "3rem", "tailwind": "text-5xl", "line_height": "1"},
        },
    },
}

# 8pt spacing system
SPACING_SYSTEM = {
    "compact": {
        "name": "Compact (good for dashboards, data-heavy UIs)",
        "scale": {
            "2xs": {"value": "0.25rem", "px": "4px", "tailwind": "1"},
            "xs": {"value": "0.5rem", "px": "8px", "tailwind": "2"},
            "sm": {"value": "0.75rem", "px": "12px", "tailwind": "3"},
            "md": {"value": "1rem", "px": "16px", "tailwind": "4"},
            "lg": {"value": "1.5rem", "px": "24px", "tailwind": "6"},
            "xl": {"value": "2rem", "px": "32px", "tailwind": "8"},
            "2xl": {"value": "3rem", "px": "48px", "tailwind": "12"},
            "section": {"value": "4rem", "px": "64px", "tailwind": "16"},
        },
    },
    "comfortable": {
        "name": "Comfortable (general purpose, most apps)",
        "scale": {
            "2xs": {"value": "0.25rem", "px": "4px", "tailwind": "1"},
            "xs": {"value": "0.5rem", "px": "8px", "tailwind": "2"},
            "sm": {"value": "1rem", "px": "16px", "tailwind": "4"},
            "md": {"value": "1.5rem", "px": "24px", "tailwind": "6"},
            "lg": {"value": "2rem", "px": "32px", "tailwind": "8"},
            "xl": {"value": "3rem", "px": "48px", "tailwind": "12"},
            "2xl": {"value": "4rem", "px": "64px", "tailwind": "16"},
            "section": {"value": "6rem", "px": "96px", "tailwind": "24"},
        },
    },
    "spacious": {
        "name": "Spacious (marketing, landing pages, luxury)",
        "scale": {
            "2xs": {"value": "0.5rem", "px": "8px", "tailwind": "2"},
            "xs": {"value": "1rem", "px": "16px", "tailwind": "4"},
            "sm": {"value": "1.5rem", "px": "24px", "tailwind": "6"},
            "md": {"value": "2rem", "px": "32px", "tailwind": "8"},
            "lg": {"value": "3rem", "px": "48px", "tailwind": "12"},
            "xl": {"value": "4rem", "px": "64px", "tailwind": "16"},
            "2xl": {"value": "6rem", "px": "96px", "tailwind": "24"},
            "section": {"value": "8rem", "px": "128px", "tailwind": "32"},
        },
    },
}


def generate_color_palette(primary_hex: str, mode: str = "both") -> dict:
    """Generate a complete color palette from a primary color."""
    r, g, b = hex_to_rgb(primary_hex)
    h, s, l = rgb_to_hsl(r, g, b)
    
    def hsl_to_hex(h: float, s: float, l: float) -> str:
        r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    # Generate shade scale (50-950)
    shades = {}
    shade_levels = [
        ("50", 97), ("100", 94), ("200", 86), ("300", 76),
        ("400", 64), ("500", 50), ("600", 40), ("700", 32),
        ("800", 24), ("900", 17), ("950", 10),
    ]
    for name, lightness in shade_levels:
        # Adjust saturation: boost in mid-tones, reduce at extremes
        sat_adjust = s * (1 - abs(lightness - 50) / 80)
        shades[name] = hsl_to_hex(h, max(5, min(100, sat_adjust)), lightness)
    
    # Generate complementary accent
    accent_h = (h + 180) % 360
    accent = hsl_to_hex(accent_h, min(s * 0.8, 80), 50)
    
    # Generate analogous colors
    analogous_1 = hsl_to_hex((h + 30) % 360, s * 0.9, 50)
    analogous_2 = hsl_to_hex((h - 30) % 360, s * 0.9, 50)
    
    # Semantic colors (universal)
    semantic = {
        "success": "#22c55e",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6",
    }
    
    palette = {
        "primary": {
            "hex": primary_hex,
            "shades": shades,
            "usage": "Main brand color, CTAs, active states, links",
        },
        "accent": {
            "hex": accent,
            "usage": "Secondary actions, highlights, badges",
        },
        "analogous": [analogous_1, analogous_2],
        "semantic": semantic,
    }
    
    if mode in ("both", "light"):
        palette["light_theme"] = {
            "background": "#ffffff",
            "background_secondary": shades["50"],
            "foreground": shades["950"],
            "foreground_secondary": shades["600"],
            "border": shades["200"],
            "input": shades["200"],
            "ring": shades["400"],
            "card": "#ffffff",
            "muted": shades["100"],
            "muted_foreground": shades["500"],
        }
    
    if mode in ("both", "dark"):
        palette["dark_theme"] = {
            "background": shades["950"],
            "background_secondary": shades["900"],
            "foreground": shades["50"],
            "foreground_secondary": shades["400"],
            "border": shades["800"],
            "input": shades["800"],
            "ring": shades["300"],
            "card": shades["900"],
            "muted": shades["800"],
            "muted_foreground": shades["400"],
        }
    
    # Generate CSS variables
    palette["css_variables"] = _generate_css_vars(palette)
    
    return palette


def _generate_css_vars(palette: dict) -> dict:
    """Generate CSS variable definitions from palette."""
    result = {}
    
    if "light_theme" in palette:
        light_vars = {}
        for key, val in palette["light_theme"].items():
            css_key = f"--color-{key.replace('_', '-')}"
            light_vars[css_key] = val
        light_vars["--color-primary"] = palette["primary"]["hex"]
        result["light"] = light_vars
    
    if "dark_theme" in palette:
        dark_vars = {}
        for key, val in palette["dark_theme"].items():
            css_key = f"--color-{key.replace('_', '-')}"
            dark_vars[css_key] = val
        dark_vars["--color-primary"] = palette["primary"]["hex"]
        result["dark"] = dark_vars
    
    return result


def analyze_visual(source_code: str) -> dict:
    """
    Run all visual design detectors on source code.
    
    Returns findings about color, spacing, typography, and visual hierarchy.
    """
    if not source_code or not source_code.strip():
        return {
            "findings": [],
            "severity_summary": {"errors": 0, "warnings": 0, "info": 0},
            "colors_found": [],
        }
    
    all_findings = []
    detectors = [
        detect_color_contrast_issues,
        detect_color_palette_issues,
        detect_spacing_inconsistency,
        detect_typography_issues,
        detect_visual_hierarchy,
        detect_dark_mode_issues,
    ]
    
    for detector in detectors:
        try:
            results = detector(source_code)
            all_findings.extend(results)
        except Exception:
            continue
    
    severity_summary = {"errors": 0, "warnings": 0, "info": 0}
    for f in all_findings:
        sev = f.get("severity", "info")
        severity_summary[sev + "s" if sev != "info" else sev] = severity_summary.get(sev + "s" if sev != "info" else sev, 0) + 1
    
    # Fix counting
    severity_summary = {"errors": 0, "warnings": 0, "info": 0}
    for f in all_findings:
        sev = f.get("severity", "info")
        if sev == "error":
            severity_summary["errors"] += 1
        elif sev == "warning":
            severity_summary["warnings"] += 1
        else:
            severity_summary["info"] += 1
    
    return {
        "findings": all_findings,
        "severity_summary": severity_summary,
        "colors_found": extract_colors(source_code)[:20],  # First 20
    }
