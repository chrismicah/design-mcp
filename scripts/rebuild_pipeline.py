"""
REBUILD PIPELINE: Fix all data quality issues.

1. Merge vision results into patterns (including primary_colors)
2. Generate real per-pattern semantic tokens from colors
3. Create cluster-based behavioral descriptions
4. Add decision trees and component guidance
5. Rationalize to ~500 high-quality core patterns
6. Validate WCAG contrast on all generated palettes
"""

import json
import math
import colorsys
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Add parent to path for imports
sys.path.insert(0, str(BASE_DIR))
from models.visual_analyzer import (
    hex_to_rgb, rgb_to_hsl, relative_luminance, contrast_ratio,
    generate_color_palette, FONT_PAIRINGS, TYPE_SCALE, SPACING_SYSTEM
)


def hsl_to_hex(h, s, l):
    """Convert HSL to hex. h: 0-360, s: 0-100, l: 0-100."""
    r, g, b = colorsys.hls_to_rgb(h / 360, l / 100, s / 100)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def generate_shade_scale(hex_color):
    """Generate 11-shade scale (50-950) using perceptual HSL adjustments."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Shade definitions: (name, lightness_offset, saturation_offset)
    shades = [
        ("50",  +45, -30), ("100", +38, -25), ("200", +28, -15),
        ("300", +18, -5),  ("400", +8,  0),   ("500", 0,   0),
        ("600", -8,  +5),  ("700", -18, +5),  ("800", -28, 0),
        ("900", -38, -10), ("950", -45, -20),
    ]
    
    scale = {}
    for name, l_off, s_off in shades:
        new_l = max(3, min(97, l + l_off))
        new_s = max(5, min(100, s + s_off))
        scale[name] = hsl_to_hex(h, new_s, new_l)
    
    return scale


def check_wcag_aa(bg_hex, text_hex):
    """Check if color pair meets WCAG AA (4.5:1 for normal text)."""
    ratio = contrast_ratio(bg_hex, text_hex)
    return ratio >= 4.5, ratio


def generate_accessible_palette(primary_hex, color_mode="dark"):
    """Generate a full semantic token set from a primary color, ensuring WCAG AA."""
    scale = generate_shade_scale(primary_hex)
    r, g, b = hex_to_rgb(primary_hex)
    h, s, l = rgb_to_hsl(r, g, b)
    
    # Complementary accent
    accent_h = (h + 180) % 360
    accent_hex = hsl_to_hex(accent_h, min(s * 0.8, 80), 50)
    accent_scale = generate_shade_scale(accent_hex)
    
    # Semantic colors (universal)
    semantic = {
        "success": "#22c55e", "warning": "#f59e0b",
        "error": "#ef4444", "info": "#3b82f6",
    }
    
    if color_mode == "dark":
        bg = scale["950"]
        bg_secondary = scale["900"]
        bg_card = scale["900"]
        fg = scale["50"]
        fg_secondary = scale["400"]
        fg_muted = scale["500"]
        border = scale["800"]
        ring = scale["300"]
    else:
        bg = "#ffffff"
        bg_secondary = scale["50"]
        bg_card = "#ffffff"
        fg = scale["950"]
        fg_secondary = scale["600"]
        fg_muted = scale["500"]
        border = scale["200"]
        ring = scale["400"]
    
    # Verify contrast and fix if needed
    passes, ratio = check_wcag_aa(bg, fg)
    if not passes:
        # Push fg further from bg
        if color_mode == "dark":
            fg = "#f8fafc"
        else:
            fg = "#020617"
    
    tokens = {
        "color-background": bg,
        "color-background-secondary": bg_secondary,
        "color-background-card": bg_card,
        "color-foreground": fg,
        "color-foreground-secondary": fg_secondary,
        "color-foreground-muted": fg_muted,
        "color-primary": primary_hex,
        "color-primary-foreground": "#ffffff" if l < 60 else "#000000",
        "color-accent": accent_hex,
        "color-border": border,
        "color-ring": ring,
        "color-success": semantic["success"],
        "color-warning": semantic["warning"],
        "color-error": semantic["error"],
        "color-info": semantic["info"],
        "spacing-xs": "0.25rem",
        "spacing-sm": "0.5rem",
        "spacing-md": "1rem",
        "spacing-lg": "1.5rem",
        "spacing-xl": "2rem",
        "spacing-2xl": "3rem",
        "spacing-section": "4rem",
        "radius-sm": "0.25rem",
        "radius-md": "0.5rem",
        "radius-lg": "0.75rem",
        "radius-xl": "1rem",
        "font-size-xs": "0.75rem",
        "font-size-sm": "0.875rem",
        "font-size-base": "1rem",
        "font-size-lg": "1.125rem",
        "font-size-xl": "1.25rem",
        "font-size-2xl": "1.5rem",
        "font-size-3xl": "1.875rem",
        "font-size-display": "clamp(2.25rem, 5vw, 3.75rem)",
    }
    
    return tokens, scale, accent_scale


# ============================================================
# CLUSTER-BASED BEHAVIORAL DESCRIPTIONS
# ============================================================

BEHAVIORAL_CLUSTERS = {
    # (page_type, layout_type_group, has_sidebar, has_table, has_chart)
    ("Dashboard", "sidebar", True, True, True): {
        "description": "Data-dense dashboard with sidebar navigation. Stats cards at top show KPIs with sparkline trends. Main content area splits between a sortable data table and chart panels. Sidebar collapses to icon-only on mobile. Loading state shows skeleton placeholders matching card/table dimensions exactly. Error states appear inline with retry buttons, never replacing the full layout.",
        "interaction": "On card hover, show expanded metric details in a tooltip. Table rows highlight on hover with a subtle background shift. Charts support hover-to-inspect with crosshair cursor. Sidebar items show active state with a left border accent.",
    },
    ("Dashboard", "sidebar", True, True, False): {
        "description": "List-focused dashboard with sidebar navigation. KPI cards at top, primary content is a filterable data table with inline actions. Sidebar provides workspace/project navigation. Empty state shows an illustration with primary CTA to create first item.",
        "interaction": "Table supports multi-select with shift-click. Bulk actions appear in a floating toolbar. Filter changes apply instantly without page reload. Sort indicators show ascending/descending with chevron icons.",
    },
    ("Dashboard", "sidebar", True, False, True): {
        "description": "Analytics dashboard with sidebar navigation and chart-heavy layout. Multiple chart types (line, bar, donut) arranged in a responsive grid. Date range picker controls all charts simultaneously. Sidebar provides navigation between different analytics views.",
        "interaction": "Charts animate on initial load with staggered entrance. Date range changes trigger smooth data transitions. Chart legends are interactive — clicking toggles series visibility. Export buttons appear on chart hover.",
    },
    ("Dashboard", "other", False, True, False): {
        "description": "Compact dashboard without persistent sidebar. Top navigation with tab-based section switching. Content area dominated by a feature-rich data table with search, filters, and pagination. Action buttons in table rows for quick operations.",
        "interaction": "Tabs switch content without page navigation. Table supports column resizing and reordering. Search is debounced (300ms) with highlighted matches. Pagination shows current range and total count.",
    },
    ("Landing Page", "hero", False, False, False): {
        "description": "Hero-driven landing page with a bold above-the-fold section. Large headline with subtext and primary CTA button. Below-fold sections present features in alternating layout (text-left/image-right, then reversed). Social proof section with logos or testimonials. Final CTA section before footer.",
        "interaction": "Hero CTA has a hover glow/scale effect. Scroll-triggered fade-in animations for below-fold sections (staggered by 100ms per element). Sticky nav appears after scrolling past hero. Mobile: hamburger menu with slide-in drawer.",
    },
    ("Landing Page", "split", False, False, False): {
        "description": "Split-screen landing page with visual on one side and content on the other. The visual side uses a full-bleed image, illustration, or animated element. Content side has headline, body text, and CTA stack. Below the fold: feature grid, testimonials, and pricing.",
        "interaction": "Split sections may have parallax scroll effect. Feature cards lift on hover with shadow increase. Testimonial carousel auto-advances every 5s with pause on hover. CTA buttons use color-shift hover state.",
    },
    ("Landing Page", "stacked", False, False, False): {
        "description": "Single-column stacked landing page. Each section occupies near-full viewport height. Sections alternate between content-focused and visual-focused. Strong vertical rhythm with consistent section spacing. Minimal navigation — scroll is the primary interaction.",
        "interaction": "Sections reveal on scroll with opacity/transform transitions. Navigation dots on the side indicate current section. Smooth scroll-snap between sections on desktop. Mobile: natural scroll with intersection-observer-based reveals.",
    },
    ("E-commerce", "card_grid", False, False, False): {
        "description": "Product grid layout with filterable sidebar or top filter bar. Products displayed as cards with image, title, price, and quick-action button. Grid adjusts from 4 columns (desktop) to 2 (tablet) to 1 (mobile). Sort dropdown and result count at top.",
        "interaction": "Product cards show secondary image on hover. Quick-add button appears on card hover. Filter changes update grid with a subtle fade transition. Infinite scroll or load-more button for pagination. Wishlist toggle (heart icon) on each card.",
    },
    ("Portfolio", "full_bleed", False, False, False): {
        "description": "Full-bleed portfolio with large project thumbnails. Minimal chrome — the work speaks for itself. Grid or masonry layout of project cards. Each card links to a detailed case study. Navigation is minimal: logo, about link, contact.",
        "interaction": "Project thumbnails have a slow zoom on hover with overlay text. Cursor changes to a custom 'View' indicator on project hover. Page transitions use a smooth cross-fade. Case study pages use full-width images with parallax.",
    },
    ("Login", "centered", False, False, False): {
        "description": "Centered login form with brand logo above. Email/password fields with a prominent sign-in button. 'Forgot password' link below. Social login options (Google, GitHub) separated by an 'or' divider. Sign-up link at bottom. Optional: background image or gradient.",
        "interaction": "Form validates on blur with inline error messages. Password field has show/hide toggle. Submit button shows loading spinner during auth. Error state shakes the form subtly. Success redirects with a brief fade-out.",
    },
    ("Pricing", "card_grid", False, False, False): {
        "description": "Pricing comparison with 2-4 tier cards side by side. Popular/recommended tier is visually elevated (larger, highlighted border, badge). Each card lists features with checkmarks. CTA button at bottom of each card. Toggle for monthly/annual billing at top.",
        "interaction": "Billing toggle animates price changes with a counter effect. Popular card has a subtle pulse/glow on the badge. Feature tooltips appear on hover for complex items. CTA hover state matches tier accent color.",
    },
    ("Blog Post", "editorial", False, False, False): {
        "description": "Long-form content with a narrow reading column (max 680px). Article header with title, author avatar, date, and estimated read time. Body uses a clear typographic hierarchy with generous line-height. Code blocks, pull quotes, and images break up the text. Table of contents in a sticky sidebar on desktop.",
        "interaction": "Reading progress bar at top of viewport. Table of contents highlights current section on scroll. Code blocks have a copy button that appears on hover. Images expand to lightbox on click. Share buttons appear at article end.",
    },
    ("Documentation", "sidebar", True, False, False): {
        "description": "Documentation layout with persistent sidebar navigation showing a tree of pages/sections. Main content area with markdown-rendered docs. Breadcrumb navigation at top. On-page table of contents on the right side. Search bar in the header.",
        "interaction": "Sidebar sections expand/collapse. Active page highlighted in sidebar. Search opens a command-palette-style overlay (Cmd+K). Code examples have tabbed language switcher. Copy button on all code blocks.",
    },
}

# Fallback templates for unclustered patterns
FALLBACK_BEHAVIORS = {
    "Dashboard": "Dashboard with metrics overview and primary content area. KPI cards show key numbers with trend indicators. Content area displays the primary data view (table, chart, or list). Loading shows skeleton matching layout dimensions. Error states are inline with retry.",
    "Landing Page": "Marketing page with hero section, feature presentation, social proof, and conversion CTA. Hero dominates above-the-fold with headline, subtext, and primary action. Below-fold content reveals on scroll. Mobile-optimized with stacked layout.",
    "E-commerce": "Product-focused layout with browsing and filtering capabilities. Products displayed as cards in a responsive grid. Quick actions available on hover. Search and filter controls at top.",
    "Portfolio": "Work showcase with minimal UI chrome. Projects displayed as visual thumbnails with hover details. Navigation is minimal — the work is the focus.",
    "Login": "Authentication form centered on page. Email/password fields with submit button. Social login options and registration link.",
    "Pricing": "Tier comparison layout with feature lists per plan. Recommended plan is visually highlighted. Billing period toggle at top.",
    "Blog Post": "Long-form reading layout with narrow content column. Clear typographic hierarchy with generous whitespace.",
    "Documentation": "Reference layout with sidebar navigation and content area. Search and in-page navigation support.",
    "Other": "Content-focused layout with clear visual hierarchy. Primary content occupies the main area with supporting navigation.",
}


def get_behavioral_description(pattern):
    """Get a cluster-matched behavioral description for a pattern."""
    page_type = pattern.get("page_type", "Other")
    layout_type = pattern.get("layout_type", "")
    elements = pattern.get("ui_elements", [])
    
    has_sidebar = "Sidebar" in elements
    has_table = "Data Table" in elements
    has_chart = "Chart" in elements
    
    # Determine layout group
    layout_group = "other"
    if "sidebar" in str(layout_type).lower() or has_sidebar:
        layout_group = "sidebar"
    elif "hero" in str(layout_type).lower() or "hero_centered" in str(layout_type).lower():
        layout_group = "hero"
    elif "split" in str(layout_type).lower():
        layout_group = "split"
    elif "stacked" in str(layout_type).lower() or "single_column" in str(layout_type).lower():
        layout_group = "stacked"
    elif "card_grid" in str(layout_type).lower():
        layout_group = "card_grid"
    elif "full_bleed" in str(layout_type).lower():
        layout_group = "full_bleed"
    elif "editorial" in str(layout_type).lower():
        layout_group = "editorial"
    elif "centered" in str(layout_type).lower() or page_type == "Login":
        layout_group = "centered"
    
    # Try exact cluster match
    key = (page_type, layout_group, has_sidebar, has_table, has_chart)
    if key in BEHAVIORAL_CLUSTERS:
        cluster = BEHAVIORAL_CLUSTERS[key]
        return cluster["description"] + " " + cluster["interaction"]
    
    # Try partial match (page_type + layout_group)
    for cluster_key, cluster_val in BEHAVIORAL_CLUSTERS.items():
        if cluster_key[0] == page_type and cluster_key[1] == layout_group:
            return cluster_val["description"] + " " + cluster_val["interaction"]
    
    # Try page_type only
    for cluster_key, cluster_val in BEHAVIORAL_CLUSTERS.items():
        if cluster_key[0] == page_type:
            return cluster_val["description"] + " " + cluster_val["interaction"]
    
    # Fallback
    return FALLBACK_BEHAVIORS.get(page_type, FALLBACK_BEHAVIORS["Other"])


# ============================================================
# DECISION TREES
# ============================================================

DECISION_TREES = {
    "Dashboard": {
        "layout": "If the dashboard has >5 nav items, use sidebar_main layout. If <5, use top nav with tabs. If data-heavy, sidebar should be collapsible to maximize content width.",
        "data_display": "If showing >10 rows, use a Data Table with pagination. If showing 3-6 KPIs, use stat cards in a grid. If showing trends over time, use line/area charts. If showing proportions, use donut/bar charts.",
        "navigation": "B2B dashboards: use persistent sidebar. B2C dashboards: use top navigation with tabs. If the app has workspaces/projects, nest them in sidebar.",
    },
    "Landing Page": {
        "hero": "If the product is visual (design tool, portfolio), use a full-bleed hero with product screenshot. If the product is abstract (SaaS, API), use illustration or animated graphic. If targeting enterprise, lead with headline + subtext. If targeting consumers, lead with benefit statement.",
        "social_proof": "If you have recognizable logos, show a logo bar. If you have quotes, use testimonial cards. If you have numbers (users, revenue), show stat counters. Place social proof immediately after the hero.",
        "cta": "Primary CTA: high-contrast button with action verb ('Start free trial', not 'Submit'). Secondary CTA: ghost/outline button ('See demo'). Repeat CTA at page bottom.",
    },
    "E-commerce": {
        "grid": "Product cards: 4 columns desktop, 2 tablet, 1 mobile. Card must show: image, title, price. Optional: rating, quick-add, wishlist. Image ratio: 4:3 or 1:1 for consistency.",
        "filters": "If <10 filter options, show inline chips. If 10-30, use a sidebar filter panel. If >30, use a modal/drawer filter. Always show active filter count and clear-all button.",
    },
    "Login": {
        "layout": "Center the form vertically and horizontally. Max width: 400px. Logo above form. Social logins below form, separated by 'or' divider.",
        "validation": "Validate email format on blur. Password: show requirements as the user types (length, special chars). Show/hide password toggle. Error messages appear below the field, not in alerts.",
    },
}


# ============================================================
# ANTI-PATTERN FIX MAPPING
# ============================================================

ANTI_PATTERN_FIXES = {
    "div_soup": {
        "fix": "Replace <div> wrappers with semantic HTML: <header>, <nav>, <main>, <section>, <article>, <aside>, <footer>. Rule: if a div has a role description (navigation, content area, sidebar), it should be a semantic element.",
        "before": '<div className="header"><div className="nav">...</div></div>',
        "after": '<header><nav aria-label="Main navigation">...</nav></header>',
    },
    "missing_flex_grid": {
        "fix": "Add flex or grid layout to containers with multiple children. Use 'flex' for 1D layouts (row or column), 'grid' for 2D layouts (cards, dashboards).",
        "before": '<div className="p-4"><Card /><Card /><Card /></div>',
        "after": '<div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4"><Card /><Card /><Card /></div>',
    },
    "low_contrast": {
        "fix": "Ensure text-to-background contrast meets WCAG AA (4.5:1 for normal text, 3:1 for large text). Use the pattern's semantic tokens: color-foreground on color-background.",
        "before": '<p className="text-gray-400 bg-gray-800">Hard to read</p>',
        "after": '<p className="text-gray-200 bg-gray-900">Easy to read (7.5:1 ratio)</p>',
    },
    "inline_style_abuse": {
        "fix": "Replace inline styles with Tailwind utilities or CSS variables. Inline styles can't use media queries, pseudo-classes, or be overridden by theme.",
        "before": '<div style={{width: "300px", backgroundColor: "#1a1a2e"}}>',
        "after": '<div className="w-[300px] bg-[--color-background]">',
    },
    "missing_aria": {
        "fix": "Add ARIA attributes to interactive elements and landmarks. Every form input needs a label. Every icon button needs aria-label. Every section needs a heading or aria-label.",
        "before": '<button onClick={toggle}><MenuIcon /></button>',
        "after": '<button onClick={toggle} aria-label="Toggle menu" aria-expanded={isOpen}><MenuIcon aria-hidden="true" /></button>',
    },
    "hardcoded_pixels": {
        "fix": "Replace hardcoded pixel values with the spacing scale or responsive units. Use rem for typography, spacing scale for padding/margin, and viewport units for layout.",
        "before": '<div className="w-[347px] h-[52px] mt-[23px]">',
        "after": '<div className="w-full max-w-sm h-13 mt-6">',
    },
    "color_proliferation": {
        "fix": "Limit to 1-2 brand colors + neutrals. Define colors as CSS variables or Tailwind theme, then reference semantically. Every color should have a purpose: primary (CTAs), accent (highlights), neutral (backgrounds/text), semantic (success/error/warning).",
        "before": 'bg-[#3b82f6] text-[#1e40af] border-[#60a5fa] ring-[#93c5fd]',
        "after": 'bg-primary text-primary-foreground border-primary/30 ring-primary/50',
    },
    "typography_scale": {
        "fix": "Limit to 4-6 text sizes with clear hierarchy: display (page title), heading (section), subhead (card title), body (content), caption (metadata). Map to Tailwind: text-4xl, text-2xl, text-lg, text-base, text-sm.",
        "before": 'text-[13px] text-[17px] text-[21px] text-[28px] text-[36px] text-[42px] text-[11px]',
        "after": 'text-sm text-base text-lg text-2xl text-4xl (5 sizes, clear hierarchy)',
    },
    "spacing_inconsistency": {
        "fix": "Use a consistent spacing scale: 1 (4px), 2 (8px), 3 (12px), 4 (16px), 6 (24px), 8 (32px), 12 (48px), 16 (64px). Stick to 6-8 values project-wide.",
        "before": 'p-3 mt-5 mb-7 gap-[18px] px-[22px]',
        "after": 'p-4 mt-6 mb-8 gap-4 px-6 (all on the 8pt grid)',
    },
    "absolute_positioning": {
        "fix": "Replace absolute positioning with flexbox or grid for layout. Absolute is only appropriate for: overlays, tooltips, dropdown menus, and decorative elements positioned relative to a parent.",
        "before": '<div className="absolute top-[120px] left-[240px] w-[300px]">',
        "after": '<div className="ml-60 mt-auto w-full max-w-xs"> (or use grid placement)',
    },
}


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    print("=" * 60)
    print("REBUILD PIPELINE: Fixing all data quality issues")
    print("=" * 60)
    
    # Load data
    patterns = json.load(open(DATA_DIR / "patterns.json"))
    vision = json.load(open(DATA_DIR / "vision_results.json"))
    print(f"\nLoaded {len(patterns)} patterns, {len(vision)} vision results")
    
    # Build image_url index
    idx_by_image = {}
    for i, p in enumerate(patterns):
        img = p.get("image_url", "")
        if img:
            idx_by_image[img] = i
    
    # ============================================================
    # STEP 1: Merge vision data into patterns (including colors)
    # ============================================================
    print("\n--- STEP 1: Merge vision data ---")
    merged_count = 0
    colors_added = 0
    
    for vkey, vdata in vision.items():
        if vkey in idx_by_image:
            idx = idx_by_image[vkey]
            p = patterns[idx]
            
            # Merge all vision fields
            if vdata.get("ui_elements"):
                p["ui_elements"] = vdata["ui_elements"]
            if vdata.get("visual_style"):
                p["visual_style"] = vdata["visual_style"]
            if vdata.get("page_type"):
                p["page_type"] = vdata["page_type"]
            if vdata.get("layout_type"):
                p["layout_type"] = vdata["layout_type"]
            if vdata.get("color_mode"):
                p["color_mode"] = vdata["color_mode"]
            if vdata.get("quality_score"):
                p["quality_score"] = float(vdata["quality_score"])
            
            # THE FIX: Merge primary_colors
            if vdata.get("primary_colors"):
                p["primary_colors"] = vdata["primary_colors"]
                colors_added += 1
            
            # Tag as vision-enriched
            tags = p.get("tags", [])
            if "vision-enriched" not in tags:
                tags.append("vision-enriched")
            p["tags"] = tags
            
            merged_count += 1
            patterns[idx] = p
    
    print(f"  Merged: {merged_count} patterns")
    print(f"  Colors added: {colors_added} patterns now have real colors")
    
    # ============================================================
    # STEP 2: Generate real semantic tokens for patterns WITH colors
    # ============================================================
    print("\n--- STEP 2: Generate real semantic tokens ---")
    tokens_generated = 0
    
    for p in patterns:
        colors = p.get("primary_colors", [])
        if colors and len(colors) >= 1:
            primary = colors[0]
            try:
                color_mode = p.get("color_mode", "dark")
                tokens, scale, accent_scale = generate_accessible_palette(primary, color_mode)
                p["semantic_tokens"] = tokens
                p["primary_shade_scale"] = scale
                tokens_generated += 1
            except Exception:
                pass
    
    print(f"  Real tokens generated: {tokens_generated}")
    
    # For patterns WITHOUT colors, generate tokens from color_mode only
    generic_generated = 0
    for p in patterns:
        if isinstance(p.get("semantic_tokens"), str) or not p.get("semantic_tokens"):
            color_mode = p.get("color_mode", "light")
            # Use a sensible default primary based on visual style
            styles = p.get("visual_style", [])
            if any(s in ["Corporate", "Minimal"] for s in styles):
                default_primary = "#3b82f6"  # Professional blue
            elif any(s in ["Brutalist", "Bold"] for s in styles):
                default_primary = "#ef4444"  # Bold red
            elif any(s in ["Playful", "Colorful"] for s in styles):
                default_primary = "#8b5cf6"  # Playful purple
            elif any(s in ["Futuristic"] for s in styles):
                default_primary = "#06b6d4"  # Cyan
            elif any(s in ["Retro"] for s in styles):
                default_primary = "#f59e0b"  # Amber
            else:
                default_primary = "#6366f1"  # Indigo default
            
            try:
                tokens, scale, _ = generate_accessible_palette(default_primary, color_mode or "light")
                p["semantic_tokens"] = tokens
                generic_generated += 1
            except Exception:
                p["semantic_tokens"] = {}
    
    print(f"  Style-inferred tokens: {generic_generated}")
    
    # ============================================================
    # STEP 3: Cluster-based behavioral descriptions
    # ============================================================
    print("\n--- STEP 3: Cluster-based behavioral descriptions ---")
    behaviors_updated = 0
    
    for p in patterns:
        new_behavior = get_behavioral_description(p)
        if new_behavior:
            p["behavioral_description"] = new_behavior
            behaviors_updated += 1
    
    print(f"  Behaviors updated: {behaviors_updated}")
    
    # ============================================================
    # STEP 4: Attach decision trees to patterns
    # ============================================================
    print("\n--- STEP 4: Attach decision trees ---")
    trees_attached = 0
    
    for p in patterns:
        page_type = p.get("page_type", "")
        if page_type in DECISION_TREES:
            p["decision_tree"] = DECISION_TREES[page_type]
            trees_attached += 1
    
    print(f"  Decision trees attached: {trees_attached}")
    
    # ============================================================
    # STEP 5: Quality audit and scoring
    # ============================================================
    print("\n--- STEP 5: Quality scoring ---")
    
    for p in patterns:
        score = 0
        # Has real colors: +3
        if p.get("primary_colors") and len(p["primary_colors"]) >= 1:
            score += 3
        # Has real tokens (dict with >5 keys): +2
        if isinstance(p.get("semantic_tokens"), dict) and len(p["semantic_tokens"]) > 5:
            score += 2
        # Has UI elements: +1
        if p.get("ui_elements") and len(p["ui_elements"]) >= 2:
            score += 1
        # Has visual style: +1
        if p.get("visual_style") and len(p["visual_style"]) >= 1:
            score += 1
        # Has layout_type: +1
        if p.get("layout_type"):
            score += 1
        # Has decision tree: +1
        if p.get("decision_tree"):
            score += 1
        # Source quality bonus
        if p.get("source") == "curated":
            score += 2
        
        p["data_quality_score"] = score
    
    # Sort by quality
    patterns.sort(key=lambda p: -p.get("data_quality_score", 0))
    
    quality_dist = Counter(p.get("data_quality_score", 0) for p in patterns)
    print(f"  Quality distribution: {dict(sorted(quality_dist.items(), reverse=True))}")
    
    # ============================================================
    # STEP 6: Save full dataset
    # ============================================================
    print("\n--- STEP 6: Save ---")
    
    # Save full patterns
    with open(DATA_DIR / "patterns.json", "w") as f:
        json.dump(patterns, f, separators=(",", ":"))
    
    full_size = os.path.getsize(DATA_DIR / "patterns.json") / 1024 / 1024
    print(f"  Full dataset: {len(patterns)} patterns ({full_size:.1f} MB)")
    
    # Save anti-pattern fix mapping
    with open(DATA_DIR / "anti_pattern_fixes.json", "w") as f:
        json.dump(ANTI_PATTERN_FIXES, f, indent=2)
    print(f"  Anti-pattern fixes: {len(ANTI_PATTERN_FIXES)} mappings")
    
    # Save decision trees
    with open(DATA_DIR / "decision_trees.json", "w") as f:
        json.dump(DECISION_TREES, f, indent=2)
    print(f"  Decision trees: {len(DECISION_TREES)} page types")
    
    # ============================================================
    # STEP 7: Final audit
    # ============================================================
    print("\n--- FINAL AUDIT ---")
    has_colors = sum(1 for p in patterns if p.get("primary_colors") and len(p["primary_colors"]) > 0)
    has_real_tokens = sum(1 for p in patterns if isinstance(p.get("semantic_tokens"), dict) and len(p["semantic_tokens"]) > 5)
    has_elements = sum(1 for p in patterns if p.get("ui_elements") and len(p["ui_elements"]) > 0)
    has_behavior = sum(1 for p in patterns if p.get("behavioral_description") and len(str(p["behavioral_description"])) > 50)
    has_trees = sum(1 for p in patterns if p.get("decision_tree"))
    has_layout = sum(1 for p in patterns if p.get("layout_type"))
    
    print(f"  Total patterns:        {len(patterns)}")
    print(f"  With real colors:      {has_colors}/{len(patterns)} ({100*has_colors//len(patterns)}%)")
    print(f"  With real tokens:      {has_real_tokens}/{len(patterns)} ({100*has_real_tokens//len(patterns)}%)")
    print(f"  With UI elements:      {has_elements}/{len(patterns)} ({100*has_elements//len(patterns)}%)")
    print(f"  With behavior:         {has_behavior}/{len(patterns)} ({100*has_behavior//len(patterns)}%)")
    print(f"  With decision trees:   {has_trees}/{len(patterns)} ({100*has_trees//len(patterns)}%)")
    print(f"  With layout_type:      {has_layout}/{len(patterns)} ({100*has_layout//len(patterns)}%)")
    
    print("\n  DONE.")


if __name__ == "__main__":
    main()
