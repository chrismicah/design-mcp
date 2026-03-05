"""
Static analysis engine for detecting UI anti-patterns in "vibecoded" code.

Detects 15 categories of anti-patterns across styling, layout, and 
structural/accessibility domains using only Python builtins (re, html.parser).
No external dependencies required.
"""

import re
from html.parser import HTMLParser
from typing import Optional


# ============================================================
# Anti-Pattern Finding dataclass (plain dict for simplicity)
# ============================================================

def finding(type: str, severity: str, message: str, 
            line: Optional[int] = None, suggestion: str = "") -> dict:
    """Create a standardized finding dict."""
    return {
        "type": type,
        "severity": severity,  # "error" | "warning" | "info"
        "message": message,
        "line": line,
        "suggestion": suggestion,
    }


# ============================================================
# STYLING DETECTORS
# ============================================================

# Regex patterns compiled once
RE_MAGIC_HEX_TAILWIND = re.compile(
    r'(?:bg|text|border|fill|stroke|ring|shadow|accent|decoration|outline|caret|from|via|to)-\[#([A-Fa-f0-9]{3,8})\]'
)
RE_MAGIC_HEX_INLINE = re.compile(
    r'''(?:color|background(?:-color)?|border(?:-color)?)\s*:\s*['"]?#([A-Fa-f0-9]{3,8})'''
)

RE_HARDCODED_PX_TAILWIND = re.compile(
    r'(?:w|h|min-w|min-h|max-w|max-h|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|top|bottom|left|right|inset|rounded|text|leading|tracking|space-x|space-y|border|ring|shadow)-\[(\d+)px\]'
)
RE_HARDCODED_PX_INLINE = re.compile(
    r'''(?:width|height|padding|margin|top|left|right|bottom|font-size|border-radius|gap)\s*:\s*['"]?(\d+)px'''
)

RE_INLINE_STYLE_REACT = re.compile(r'style\s*=\s*\{\{')
RE_INLINE_STYLE_HTML = re.compile(r'''style\s*=\s*['"][^'"]+['"]''')

RE_ZINDEX_ABUSE = re.compile(r'z-\[?(\d+)\]?')
RE_ZINDEX_TAILWIND_HIGH = re.compile(r'z-(?:50|99|999|9999)')

RE_ARBITRARY_VALUES = re.compile(
    r'-\[(\d+\.?\d*)(px|rem|em|vh|vw|%)\]'
)


def detect_magic_hex_colors(code: str) -> list[dict]:
    """Detect hardcoded hex colors that should use semantic tokens."""
    findings = []
    
    for match in RE_MAGIC_HEX_TAILWIND.finditer(code):
        hex_val = match.group(1)
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="magic_hex_color",
            severity="warning",
            message=f"Hardcoded hex color #{hex_val} in Tailwind class '{match.group()}'",
            line=line,
            suggestion=f"Replace #{hex_val} with a semantic token (e.g., bg-primary, text-foreground, border-input)"
        ))
    
    for match in RE_MAGIC_HEX_INLINE.finditer(code):
        hex_val = match.group(1)
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="magic_hex_color",
            severity="warning",
            message=f"Hardcoded hex color #{hex_val} in inline style",
            line=line,
            suggestion=f"Replace #{hex_val} with a CSS variable (e.g., var(--color-primary))"
        ))
    
    return findings


def detect_hardcoded_pixels(code: str) -> list[dict]:
    """Detect rigid pixel values that break responsiveness."""
    findings = []
    
    for match in RE_HARDCODED_PX_TAILWIND.finditer(code):
        px_val = int(match.group(1))
        line = code[:match.start()].count('\n') + 1
        # Small values (1-4px) are often intentional (borders, etc.)
        if px_val > 4:
            findings.append(finding(
                type="hardcoded_pixels",
                severity="warning",
                message=f"Hardcoded pixel value {px_val}px in '{match.group()}'",
                line=line,
                suggestion=f"Use responsive units or Tailwind scale values instead of {px_val}px"
            ))
    
    for match in RE_HARDCODED_PX_INLINE.finditer(code):
        px_val = int(match.group(1))
        line = code[:match.start()].count('\n') + 1
        if px_val > 4:
            findings.append(finding(
                type="hardcoded_pixels",
                severity="warning",
                message=f"Hardcoded pixel value {px_val}px in inline style",
                line=line,
                suggestion=f"Use rem units or CSS variables for {px_val}px"
            ))
    
    return findings


def detect_inline_styles(code: str) -> list[dict]:
    """Detect inline style abuse (style={{}} in React or style='' in HTML)."""
    findings = []
    
    for match in RE_INLINE_STYLE_REACT.finditer(code):
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="inline_style_abuse",
            severity="warning",
            message="React inline style object detected",
            line=line,
            suggestion="Replace style={{}} with Tailwind utility classes or CSS modules for media query and pseudo-class support"
        ))
    
    for match in RE_INLINE_STYLE_HTML.finditer(code):
        # Skip React-style matches (already caught above)
        if '{{' in code[max(0, match.start()-5):match.start()+5]:
            continue
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="inline_style_abuse",
            severity="warning",
            message="Inline style attribute detected",
            line=line,
            suggestion="Move inline styles to utility classes or a stylesheet"
        ))
    
    return findings


def detect_zindex_abuse(code: str) -> list[dict]:
    """Detect arbitrarily high z-index values."""
    findings = []
    
    for match in RE_ZINDEX_ABUSE.finditer(code):
        z_val = int(match.group(1))
        if z_val >= 50:
            line = code[:match.start()].count('\n') + 1
            findings.append(finding(
                type="zindex_abuse",
                severity="warning",
                message=f"High z-index value z-{z_val} forces stacking context",
                line=line,
                suggestion="Use a controlled stacking context (z-10, z-20) or fix underlying DOM structure"
            ))
    
    return findings


def detect_arbitrary_values(code: str) -> list[dict]:
    """Detect arbitrary Tailwind values that bypass design system scales."""
    findings = []
    
    for match in RE_ARBITRARY_VALUES.finditer(code):
        val = match.group(1)
        unit = match.group(2)
        full = match.group()
        line = code[:match.start()].count('\n') + 1
        
        # Skip if it's a common round value that maps to the scale
        try:
            num = float(val)
            if unit == 'px' and num in (0, 1, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64, 96):
                continue  # These map cleanly to Tailwind scale
            if unit == 'rem' and num in (0, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4):
                continue
        except ValueError:
            pass
        
        findings.append(finding(
            type="arbitrary_values",
            severity="info",
            message=f"Arbitrary value {full} bypasses design system scale",
            line=line,
            suggestion=f"Map {val}{unit} to the nearest Tailwind scale value"
        ))
    
    return findings


# ============================================================
# LAYOUT DETECTORS
# ============================================================

RE_MARGIN_HACK = re.compile(
    r'm[lrtbxy]?-\[(\d+)px\]'
)
RE_MARGIN_LARGE = re.compile(
    r'm[lrtbxy]?-(?:24|28|32|36|40|44|48|52|56|60|64|72|80|96)'
)

RE_ABSOLUTE_POS = re.compile(r'\babsolute\b')
RE_DIRECTIONAL = re.compile(r'(?:top|left|right|bottom)-\[?\d+')

RE_FIXED_VH = re.compile(r'h-\[100vh\]')
RE_FIXED_SCREEN = re.compile(r'\bh-screen\b')

RE_FLEX_GRID = re.compile(r'\b(?:flex|grid|inline-flex|inline-grid)\b')


def detect_margin_alignment(code: str) -> list[dict]:
    """Detect large margins used as layout hacks."""
    findings = []
    
    for match in RE_MARGIN_HACK.finditer(code):
        px_val = int(match.group(1))
        if px_val >= 50:
            line = code[:match.start()].count('\n') + 1
            findings.append(finding(
                type="margin_alignment_hack",
                severity="warning",
                message=f"Large margin {match.group()} used for layout positioning",
                line=line,
                suggestion="Use flexbox (justify-between, ml-auto) or grid for layout instead of large margins"
            ))
    
    for match in RE_MARGIN_LARGE.finditer(code):
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="margin_alignment_hack",
            severity="info",
            message=f"Large margin utility '{match.group()}' may indicate layout hack",
            line=line,
            suggestion="Consider using flexbox gap or auto margins instead"
        ))
    
    return findings


def detect_absolute_positioning(code: str) -> list[dict]:
    """Detect absolute positioning with explicit coordinates."""
    findings = []
    lines = code.split('\n')
    
    for i, line_text in enumerate(lines, 1):
        if RE_ABSOLUTE_POS.search(line_text) and RE_DIRECTIONAL.search(line_text):
            findings.append(finding(
                type="absolute_positioning",
                severity="warning",
                message=f"Absolute positioning with explicit coordinates",
                line=i,
                suggestion="Replace absolute positioning with flexbox or grid layout for document flow"
            ))
    
    return findings


def detect_fixed_heights(code: str) -> list[dict]:
    """Detect fixed viewport height that traps scrolling."""
    findings = []
    
    for match in RE_FIXED_VH.finditer(code):
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="fixed_viewport_height",
            severity="warning",
            message="Fixed h-[100vh] may trap scrolling on mobile",
            line=line,
            suggestion="Use min-h-screen or h-dvh (dynamic viewport height) instead"
        ))
    
    return findings


def detect_missing_flex_grid(code: str) -> list[dict]:
    """Detect containers with multiple children but no flex/grid."""
    findings = []
    
    # Simple heuristic: look for divs with className but no flex/grid
    # that seem to have multiple child elements
    div_pattern = re.compile(
        r'<div\s+(?:className|class)\s*=\s*["\']([^"\']*)["\']',
        re.IGNORECASE
    )
    
    for match in div_pattern.finditer(code):
        classes = match.group(1)
        if not RE_FLEX_GRID.search(classes):
            # Check if this div likely has multiple children by looking ahead
            start = match.end()
            # Count child elements in the next ~500 chars
            snippet = code[start:start+500]
            child_opens = len(re.findall(r'<(?:div|span|p|a|button|input|img|h[1-6])\b', snippet))
            if child_opens >= 3:
                line = code[:match.start()].count('\n') + 1
                findings.append(finding(
                    type="missing_flex_grid",
                    severity="info",
                    message=f"Container with multiple children lacks flex/grid layout",
                    line=line,
                    suggestion="Add 'flex' or 'grid' class for proper layout distribution"
                ))
    
    return findings


def detect_redundant_wrappers(code: str) -> list[dict]:
    """Detect divs that wrap a single child unnecessarily."""
    findings = []
    
    # Pattern: <div className="..."><SingleChild .../></div>
    # This is a simplified heuristic
    wrapper_pattern = re.compile(
        r'<div\s+(?:className|class)\s*=\s*["\'][^"\']*["\']\s*>\s*\n?\s*<(\w+)[^>]*/>\s*\n?\s*</div>',
        re.MULTILINE
    )
    
    for match in wrapper_pattern.finditer(code):
        child_tag = match.group(1)
        line = code[:match.start()].count('\n') + 1
        findings.append(finding(
            type="redundant_wrapper",
            severity="info",
            message=f"Wrapper div around single <{child_tag}/> element",
            line=line,
            suggestion=f"Apply wrapper styles directly to <{child_tag}/> to reduce DOM depth"
        ))
    
    return findings


# ============================================================
# STRUCTURAL / ACCESSIBILITY DETECTORS
# ============================================================

def detect_div_soup(code: str) -> list[dict]:
    """Detect deep nesting of non-semantic divs."""
    findings = []
    semantic_tags = {'main', 'header', 'footer', 'nav', 'article', 'section', 
                     'aside', 'figure', 'figcaption', 'details', 'summary',
                     'form', 'table', 'ul', 'ol', 'li'}
    
    # Track div nesting depth
    depth = 0
    max_depth = 0
    max_depth_line = 1
    
    open_tag = re.compile(r'<(div|span)\b[^/]*(?<!/)>')
    close_tag = re.compile(r'</(div|span)>')
    semantic_open = re.compile(r'<(' + '|'.join(semantic_tags) + r')\b')
    
    for i, line_text in enumerate(code.split('\n'), 1):
        # Semantic tags reset the counter
        if semantic_open.search(line_text):
            depth = 0
        
        opens = len(open_tag.findall(line_text))
        closes = len(close_tag.findall(line_text))
        depth += opens - closes
        
        if depth > max_depth:
            max_depth = depth
            max_depth_line = i
    
    if max_depth > 4:
        findings.append(finding(
            type="div_soup",
            severity="error",
            message=f"Deep div nesting detected ({max_depth} levels) without semantic HTML5 tags",
            line=max_depth_line,
            suggestion="Replace generic divs with semantic tags: <main>, <section>, <article>, <nav>, <header>, <footer>"
        ))
    
    # Also check for total lack of semantic tags
    has_semantic = bool(re.search(r'<(?:' + '|'.join(semantic_tags) + r')\b', code))
    div_count = len(re.findall(r'<div\b', code))
    if div_count > 5 and not has_semantic:
        findings.append(finding(
            type="div_soup",
            severity="warning",
            message=f"No semantic HTML5 tags found among {div_count} div elements",
            line=None,
            suggestion="Add semantic landmarks (<main>, <nav>, <section>) for screen reader navigation"
        ))
    
    return findings


RE_ONCLICK_DIV = re.compile(
    r'<(div|span)\b([^>]*?)on[Cc]lick\s*=',
    re.DOTALL
)

def detect_interactive_divs(code: str) -> list[dict]:
    """Detect onClick on div/span without role='button' or tabIndex."""
    findings = []
    
    for match in RE_ONCLICK_DIV.finditer(code):
        tag = match.group(1)
        attrs = match.group(2) + code[match.end():match.end()+200].split('>')[0]
        
        has_role = bool(re.search(r'role\s*=\s*["\']button["\']', attrs))
        has_tabindex = bool(re.search(r'tabIndex\s*=', attrs, re.IGNORECASE))
        
        if not has_role:
            line = code[:match.start()].count('\n') + 1
            msg_parts = ["missing role=\"button\""]
            if not has_tabindex:
                msg_parts.append("missing tabIndex")
            
            findings.append(finding(
                type="interactive_div",
                severity="error",
                message=f"Interactive <{tag}> with onClick but {', '.join(msg_parts)}",
                line=line,
                suggestion=f"Replace <{tag} onClick> with <button> or add role=\"button\" tabIndex={{0}} for keyboard accessibility"
            ))
    
    return findings


def detect_missing_aria(code: str) -> list[dict]:
    """Detect toggle/modal patterns without ARIA attributes."""
    findings = []
    
    # Detect toggle patterns (useState + onClick toggling) without aria-expanded
    toggle_pattern = re.compile(r'onClick\s*=\s*\{?\s*\(\)\s*=>\s*set\w+\s*\(\s*!\w+\s*\)')
    has_aria_expanded = bool(re.search(r'aria-expanded', code))
    
    if toggle_pattern.search(code) and not has_aria_expanded:
        line_match = toggle_pattern.search(code)
        line = code[:line_match.start()].count('\n') + 1 if line_match else None
        findings.append(finding(
            type="missing_aria",
            severity="error",
            message="Toggle handler found without aria-expanded attribute",
            line=line,
            suggestion="Add aria-expanded={isOpen} to the trigger element for screen reader state announcement"
        ))
    
    # Detect modal-like patterns without aria-modal
    modal_indicators = re.compile(r'(?:modal|dialog|overlay|backdrop)', re.IGNORECASE)
    has_aria_modal = bool(re.search(r'aria-modal|role\s*=\s*["\']dialog["\']', code))
    
    if modal_indicators.search(code) and not has_aria_modal:
        findings.append(finding(
            type="missing_aria",
            severity="warning",
            message="Modal/dialog pattern detected without aria-modal or role=\"dialog\"",
            line=None,
            suggestion="Add role=\"dialog\" aria-modal=\"true\" for proper focus trapping and screen reader support"
        ))
    
    return findings


RE_OUTLINE_NONE = re.compile(r'outline-none(?!.*focus:(?:ring|outline))')

def detect_missing_focus_states(code: str) -> list[dict]:
    """Detect outline removal without custom focus indicators."""
    findings = []
    
    # Check each line for outline-none without a focus ring
    for i, line_text in enumerate(code.split('\n'), 1):
        if 'outline-none' in line_text:
            # Check if there's a focus:ring or focus:outline in the same className string
            # Extract the full className value
            class_match = re.search(r'(?:className|class)\s*=\s*["\']([^"\']*outline-none[^"\']*)["\']', line_text)
            if class_match:
                class_value = class_match.group(1)
                has_focus_ring = bool(re.search(r'focus:(?:ring|outline|border|shadow)', class_value))
                has_focus_visible = bool(re.search(r'focus-visible:', class_value))
                
                if not has_focus_ring and not has_focus_visible:
                    findings.append(finding(
                        type="missing_focus_states",
                        severity="error",
                        message="outline-none removes focus indicator without custom replacement",
                        line=i,
                        suggestion="Add focus:ring-2 focus:ring-offset-2 or focus-visible:outline to maintain keyboard navigation visibility"
                    ))
    
    return findings


RE_INPUT = re.compile(r'<input\b([^>]*?)/?>', re.DOTALL | re.IGNORECASE)

def detect_unlabeled_inputs(code: str) -> list[dict]:
    """Detect input elements without associated labels or aria-label."""
    findings = []
    
    for match in RE_INPUT.finditer(code):
        attrs = match.group(1)
        
        has_aria_label = bool(re.search(r'aria-label\s*=', attrs))
        has_aria_labelledby = bool(re.search(r'aria-labelledby\s*=', attrs))
        
        # Check for id and corresponding label
        id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', attrs)
        has_label = False
        if id_match:
            input_id = id_match.group(1)
            has_label = bool(re.search(
                rf'(?:htmlFor|for)\s*=\s*["\']' + re.escape(input_id) + r'["\']',
                code
            ))
        
        # Check if it's a hidden or submit input (these don't need labels)
        input_type = re.search(r'type\s*=\s*["\'](\w+)["\']', attrs)
        if input_type and input_type.group(1) in ('hidden', 'submit', 'button', 'reset'):
            continue
        
        if not has_aria_label and not has_aria_labelledby and not has_label:
            line = code[:match.start()].count('\n') + 1
            findings.append(finding(
                type="unlabeled_input",
                severity="error",
                message="Input element without label or aria-label",
                line=line,
                suggestion="Add <label htmlFor=\"id\"> or aria-label=\"description\" for screen reader accessibility"
            ))
    
    return findings


# ============================================================
# COMPONENT TYPE INFERENCE
# ============================================================

def infer_component_type(code: str) -> str:
    """Guess what UI component the code is trying to be."""
    code_lower = code.lower()
    
    # Check function/component name first
    comp_name = re.search(r'(?:function|const)\s+(\w+)', code)
    if comp_name:
        name = comp_name.group(1).lower()
        component_map = {
            'button': 'Button', 'btn': 'Button', 'submit': 'Button',
            'card': 'Card', 'profile': 'Card', 'usercard': 'Card',
            'nav': 'Navigation Bar', 'navbar': 'Navigation Bar', 'header': 'Navigation Bar',
            'sidebar': 'Sidebar', 'sidenav': 'Sidebar',
            'modal': 'Modal', 'dialog': 'Modal', 'popup': 'Modal',
            'dropdown': 'Dropdown', 'select': 'Dropdown', 'menu': 'Dropdown',
            'form': 'Form', 'login': 'Form', 'signup': 'Form', 'register': 'Form',
            'table': 'Data Table', 'datagrid': 'Data Table', 'list': 'Data Table',
            'tab': 'Tabs', 'tabs': 'Tabs',
            'accordion': 'Accordion', 'collapse': 'Accordion',
            'toast': 'Toast', 'notification': 'Toast', 'alert': 'Toast',
            'avatar': 'Avatar', 'badge': 'Badge',
            'carousel': 'Carousel', 'slider': 'Carousel',
            'input': 'Input', 'textfield': 'Input', 'search': 'Input',
            'tooltip': 'Tooltip', 'popover': 'Popover',
            'progress': 'Progress Bar', 'loader': 'Progress Bar', 'spinner': 'Progress Bar',
            'pagination': 'Pagination', 'breadcrumb': 'Breadcrumb',
            'toggle': 'Switch', 'switch': 'Switch',
            'checkbox': 'Checkbox', 'radio': 'Radio Button',
            'dashboard': 'Dashboard', 'pricing': 'Pricing',
        }
        for keyword, comp_type in component_map.items():
            if keyword in name:
                return comp_type
    
    # Infer from content/structure
    if re.search(r'onClick.*(?:submit|save|delete|cancel)', code_lower):
        return "Button"
    if re.search(r'<select|<option|dropdown|listbox', code_lower):
        return "Dropdown"
    if re.search(r'<form|<input.*<input', code_lower, re.DOTALL):
        return "Form"
    if re.search(r'<table|<thead|<tbody|<tr', code_lower):
        return "Data Table"
    if re.search(r'<nav\b|navigation|menu.*item', code_lower):
        return "Navigation Bar"
    if re.search(r'<img.*avatar|profile.*image|user.*photo', code_lower):
        return "Card"
    if re.search(r'modal|dialog|overlay', code_lower):
        return "Modal"
    if re.search(r'tab.*panel|tab.*content', code_lower):
        return "Tabs"
    if '<input' in code_lower:
        return "Input"
    if 'onclick' in code_lower or '<button' in code_lower:
        return "Button"
    
    return "Component"


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================

ALL_DETECTORS = [
    # Styling
    detect_magic_hex_colors,
    detect_hardcoded_pixels,
    detect_inline_styles,
    detect_zindex_abuse,
    detect_arbitrary_values,
    # Layout
    detect_margin_alignment,
    detect_absolute_positioning,
    detect_fixed_heights,
    detect_missing_flex_grid,
    detect_redundant_wrappers,
    # Structural / A11y
    detect_div_soup,
    detect_interactive_divs,
    detect_missing_aria,
    detect_missing_focus_states,
    detect_unlabeled_inputs,
]


def analyze_code(source_code: str) -> dict:
    """
    Run all anti-pattern detectors on the given source code.
    
    Returns:
        dict with keys:
            - findings: list of finding dicts
            - component_type: inferred component type string
            - severity_summary: {errors: int, warnings: int, info: int}
    """
    if not source_code or not source_code.strip():
        return {
            "findings": [],
            "component_type": "Unknown",
            "severity_summary": {"errors": 0, "warnings": 0, "info": 0},
        }
    
    all_findings = []
    
    for detector in ALL_DETECTORS:
        try:
            results = detector(source_code)
            all_findings.extend(results)
        except Exception:
            # Fail gracefully — skip broken detectors
            continue
    
    # Count severities
    severity_summary = {"errors": 0, "warnings": 0, "info": 0}
    for f in all_findings:
        sev = f.get("severity", "info")
        if sev == "error":
            severity_summary["errors"] += 1
        elif sev == "warning":
            severity_summary["warnings"] += 1
        else:
            severity_summary["info"] += 1
    
    # Infer component type
    try:
        component_type = infer_component_type(source_code)
    except Exception:
        component_type = "Component"
    
    return {
        "findings": all_findings,
        "component_type": component_type,
        "severity_summary": severity_summary,
    }
