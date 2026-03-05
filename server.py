from fastmcp import FastMCP
from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase
from models.analyzer import analyze_code, infer_component_type
from typing import Optional
from pathlib import Path
import json
import os

# Resolve paths relative to this file
BASE_DIR = Path(__file__).parent

mcp = FastMCP(
    "DesignIntelligence",
    instructions="Provides AI agents with structured access to real-world design patterns, "
                 "UI blueprints, and semantic tokens for high-fidelity UI generation."
)

db = DesignDatabase(str(BASE_DIR / "data" / "patterns.json"))


# ============================================================
# TOOL 1: Search Design Patterns
# ============================================================
@mcp.tool()
async def search_design_patterns(
    query: str,
    page_type: Optional[str] = None,
    platform: Optional[str] = "web",
    industry: Optional[str] = None,
    color_mode: Optional[str] = None,
    visual_style: Optional[str] = None,
    fields: Optional[list[str]] = None,
    limit: int = 5
) -> list[dict]:
    """
    Search the design pattern database for real-world UI examples.
    Use this BEFORE generating any UI to study how established products
    handle similar design challenges.

    Args:
        query: Natural language search (e.g. 'fintech dashboard with dark mode')
        page_type: Filter by page type (e.g. 'Dashboard', 'Pricing', 'Onboarding')
        platform: Target platform ('web', 'ios', 'android')
        industry: Filter by industry (e.g. 'Fintech', 'SaaS', 'Health')
        color_mode: Filter by 'light' or 'dark'
        visual_style: Filter by style (e.g. 'Minimal', 'Glassmorphism', 'Brutalist')
        fields: Optional list of fields to return (for token efficiency)
        limit: Max results (default 5, keep low to save tokens)

    Returns:
        List of design pattern blueprints with metadata, layout info,
        behavioral descriptions, and component hints.
    """
    results = db.search(
        query=query,
        page_type=page_type,
        platform=platform,
        industry=industry,
        color_mode=color_mode,
        visual_style=visual_style,
        limit=limit
    )
    blueprints = [_to_blueprint(r) for r in results]
    if fields:
        blueprints = [{k: v for k, v in bp.items() if k in fields or k == "id"} for bp in blueprints]
    return blueprints


# ============================================================
# TOOL 2: Get Full Blueprint
# ============================================================
@mcp.tool()
async def get_design_blueprint(pattern_id: str, detailed: bool = False) -> dict:
    """
    Get the full design blueprint for a specific pattern.
    Use after search_design_patterns to get deeper details on a specific example.

    Args:
        pattern_id: The ID from search results
        detailed: If True, includes component props, accessibility notes,
                  and full semantic tokens. If False (default), returns
                  the condensed blueprint.

    Returns:
        Complete design blueprint with layout, behavior, tokens, and component structure.
    """
    pattern = db.get(pattern_id)
    if not pattern:
        return {"error": f"Pattern '{pattern_id}' not found"}
    if detailed:
        return pattern.model_dump(exclude_none=True)
    return _to_blueprint(pattern)


# ============================================================
# TOOL 3: Get Semantic Tokens
# ============================================================
@mcp.tool()
async def get_semantic_tokens(style: Optional[str] = None) -> dict:
    """
    Get semantic design tokens (Tier 2) for consistent styling.
    These tokens encode the INTENT of design decisions, not just raw values.
    Use these instead of hardcoding hex colors and pixel values.

    Args:
        style: Optional style preset ('light', 'dark', 'brand').
               Returns the default token set if not specified.

    Returns:
        W3C-format semantic tokens for colors, spacing, typography, and borders.
    """
    tokens_path = BASE_DIR / "data" / "tokens" / "semantic_tokens.json"
    with open(tokens_path) as f:
        tokens = json.load(f)
    return tokens


# ============================================================
# TOOL 4: Get Taxonomy
# ============================================================
@mcp.tool()
async def get_design_taxonomy() -> dict:
    """
    Get the full taxonomy of design categories available in the database.
    Use this to understand what page types, UX patterns, UI elements,
    industries, and visual styles you can search for.

    Returns:
        Complete taxonomy with all available filter values.
    """
    taxonomy_path = BASE_DIR / "data" / "taxonomy.json"
    with open(taxonomy_path) as f:
        return json.load(f)


# ============================================================
# TOOL 5: Get Behavioral Pattern
# ============================================================
@mcp.tool()
async def get_behavioral_pattern(pattern_name: str) -> dict:
    """
    Get the behavioral specification for a common UX pattern.
    This describes HOW a pattern should behave, not just how it looks.
    Use this for edge cases like empty states, error handling, loading sequences.

    Args:
        pattern_name: E.g. 'empty_state', 'skeleton_loading', 'error_handling',
                      'onboarding_flow', 'form_validation', 'infinite_scroll'

    Returns:
        Behavioral description including: what triggers it, expected content,
        user psychology, CTAs, and reference implementations.
    """
    behaviors = _load_behavioral_patterns()
    if pattern_name in behaviors:
        return behaviors[pattern_name]
    # Fuzzy match
    matches = [k for k in behaviors if pattern_name.lower() in k.lower()]
    if matches:
        return {k: behaviors[k] for k in matches[:3]}
    return {"error": f"Unknown pattern '{pattern_name}'", "available": list(behaviors.keys())}


# ============================================================
# TOOL 6: Compare Patterns
# ============================================================
@mcp.tool()
async def compare_design_approaches(
    page_type: str,
    limit: int = 3
) -> dict:
    """
    Compare how different products handle the same page type.
    Returns side-by-side blueprints showing different layout strategies,
    component choices, and behavioral patterns for the same type of page.

    Args:
        page_type: The page type to compare (e.g. 'Dashboard', 'Pricing')
        limit: Number of examples to compare (default 3)

    Returns:
        Comparison object with patterns and a summary of key differences.
    """
    results = db.search(page_type=page_type, limit=limit)
    return {
        "page_type": page_type,
        "examples": [_to_blueprint(r) for r in results],
        "summary": _generate_comparison_summary(results)
    }


# ============================================================
# TOOL 7: Analyze and Devibecode
# ============================================================
@mcp.tool()
async def analyze_and_devibecode(source_code: str) -> dict:
    """
    Static analysis anti-pattern detector for vibecoded UI code.
    Scans source code for 15 categories of UI anti-patterns (styling hacks,
    layout issues, accessibility gaps, structural problems) and returns
    actionable refactoring suggestions mapped to real design system data.

    Args:
        source_code: The UI source code (JSX/TSX/HTML) to analyze.

    Returns:
        Analysis results with anti-patterns found, recommended layout,
        semantic tokens, component structure suggestions, and severity summary.
    """
    try:
        analysis = analyze_code(source_code)
        findings = analysis["findings"]
        component_type = analysis["component_type"]
        severity_summary = analysis["severity_summary"]

        # Human-readable anti-pattern strings
        anti_patterns_found = []
        for f in findings:
            line_info = f" (line {f['line']})" if f.get("line") else ""
            anti_patterns_found.append(f"[{f['severity'].upper()}] {f['message']}{line_info}")

        # Refactoring suggestions (deduplicated)
        seen_suggestions = set()
        refactoring_suggestions = []
        for f in findings:
            if f["suggestion"] not in seen_suggestions:
                seen_suggestions.add(f["suggestion"])
                refactoring_suggestions.append(f["suggestion"])

        # Query DB for matching patterns based on inferred component type
        recommended_layout = {}
        semantic_tokens_to_apply = {}
        suggested_component_structure = []

        try:
            results = db.search(query=component_type, limit=3)
            if results:
                top = results[0]
                if top.layout_type:
                    recommended_layout["layout_type"] = top.layout_type.value
                if top.layout_notes:
                    recommended_layout["layout_notes"] = top.layout_notes
                if top.semantic_tokens:
                    semantic_tokens_to_apply = top.semantic_tokens
                for r in results:
                    for hint in r.component_hints:
                        suggested_component_structure.append(hint)
        except Exception:
            pass

        # If no semantic tokens from DB, provide defaults from token file
        if not semantic_tokens_to_apply:
            try:
                tokens_path = BASE_DIR / "data" / "tokens" / "semantic_tokens.json"
                with open(tokens_path) as f:
                    tokens = json.load(f)
                # Extract a flat subset relevant to common anti-patterns
                semantic_tokens_to_apply = {
                    "color": tokens.get("color", {}),
                    "spacing": tokens.get("spacing", {}),
                }
            except Exception:
                pass

        return {
            "anti_patterns_found": anti_patterns_found,
            "recommended_layout": recommended_layout,
            "semantic_tokens_to_apply": semantic_tokens_to_apply,
            "suggested_component_structure": suggested_component_structure,
            "severity_summary": severity_summary,
            "refactoring_suggestions": refactoring_suggestions,
        }

    except Exception:
        return {
            "anti_patterns_found": [],
            "recommended_layout": {},
            "semantic_tokens_to_apply": {},
            "suggested_component_structure": [],
            "severity_summary": {"errors": 0, "warnings": 0, "info": 0},
            "refactoring_suggestions": [],
        }


# ============================================================
# Helper Functions
# ============================================================

def _to_blueprint(pattern: DesignPattern) -> dict:
    """Convert a full pattern to a token-efficient blueprint."""
    blueprint = {
        "id": pattern.id,
        "name": pattern.name,
        "page_type": pattern.page_type,
        "layout_type": pattern.layout_type.value if pattern.layout_type else None,
        "layout_notes": pattern.layout_notes,
        "ux_patterns": pattern.ux_patterns,
        "ui_elements": pattern.ui_elements,
        "color_mode": pattern.color_mode,
        "visual_style": pattern.visual_style,
        "behavioral_description": pattern.behavioral_description,
        "source_url": pattern.source_url,
    }
    # Remove None values to save tokens
    return {k: v for k, v in blueprint.items() if v is not None}


def _load_behavioral_patterns() -> dict:
    """Load behavioral pattern definitions."""
    return {
        "empty_state": {
            "description": "Screen shown when there's no data to display yet.",
            "best_practice": "Stripe pattern: Educate the user on the feature's value. Show a relevant illustration. Provide a single, prominent CTA to create the first item. Never just say 'No data found'.",
            "required_elements": ["illustration_or_icon", "explanatory_heading", "benefit_description", "primary_cta"],
            "anti_patterns": ["Generic 'No data' text", "Empty white space", "Technical error messages"],
            "reference": "Stripe, Linear, Notion"
        },
        "skeleton_loading": {
            "description": "Placeholder UI shown while real content loads.",
            "best_practice": "Skeleton shapes must match the EXACT layout of the final content. Use subtle pulse animation. Never show a single generic spinner for content-heavy pages.",
            "required_elements": ["shape_matching_final_layout", "pulse_animation", "realistic_proportions"],
            "anti_patterns": ["Generic spinner", "Skeleton that doesn't match final layout", "No animation"],
            "reference": "Facebook, LinkedIn, Notion"
        },
        "error_handling": {
            "description": "How the UI responds to failed operations.",
            "best_practice": "Preserve user input. Explain what went wrong in plain language. Provide a clear retry action. For form errors, show inline validation near the field.",
            "required_elements": ["preserved_user_data", "human_readable_message", "retry_action", "inline_field_errors"],
            "anti_patterns": ["Lost form data", "Technical error codes", "Full-page error for partial failure"],
            "reference": "Stripe, GitHub"
        },
        "onboarding_flow": {
            "description": "First-time user experience after signup.",
            "best_practice": "Progressive disclosure — don't overwhelm. Collect only essential info. Show progress. Let users skip. Demonstrate value within the first 60 seconds.",
            "required_elements": ["progress_indicator", "skip_option", "value_demonstration", "minimal_required_fields"],
            "anti_patterns": ["10+ step forms", "No skip option", "Collecting non-essential data upfront"],
            "reference": "Notion, Figma, Linear"
        },
        "form_validation": {
            "description": "Real-time feedback on user input.",
            "best_practice": "Validate on blur, not on keystroke. Show success states, not just errors. Place error messages directly below the field. Use color AND text (not color alone for accessibility).",
            "required_elements": ["on_blur_validation", "inline_error_placement", "success_indicators", "accessible_error_text"],
            "anti_patterns": ["Validation on every keystroke", "Error summary only at top", "Color-only error indicators"],
            "reference": "Stripe Elements, GitHub"
        },
        "infinite_scroll": {
            "description": "Loading more content as the user scrolls down.",
            "best_practice": "Show a loading indicator at the bottom. Preserve scroll position on back navigation. Provide a 'Back to top' button after several loads. Consider virtualization for 100+ items.",
            "required_elements": ["bottom_loading_indicator", "scroll_position_preservation", "back_to_top_affordance"],
            "anti_patterns": ["No loading indicator", "Losing position on back button", "Loading everything into DOM"],
            "reference": "Twitter/X, Instagram, Pinterest"
        },
        "command_palette": {
            "description": "Quick-access search and action modal (Cmd+K pattern).",
            "best_practice": "Activate via Cmd/Ctrl+K. Show recent actions first. Support fuzzy search. Group results by category. Keyboard navigation with highlighted selection.",
            "required_elements": ["keyboard_shortcut_trigger", "search_input", "categorized_results", "keyboard_navigation", "recent_actions"],
            "anti_patterns": ["Mouse-only interaction", "No fuzzy matching", "Flat uncategorized list"],
            "reference": "Linear, Vercel, Raycast, VS Code"
        }
    }


def _generate_comparison_summary(patterns: list[DesignPattern]) -> str:
    """Generate a brief comparison summary of the patterns."""
    if not patterns:
        return "No patterns found for comparison."
    layouts = set(p.layout_type.value for p in patterns if p.layout_type)
    styles = set(s for p in patterns for s in p.visual_style)
    return (
        f"Compared {len(patterns)} approaches. "
        f"Layout strategies: {', '.join(layouts) if layouts else 'varied'}. "
        f"Visual styles: {', '.join(styles) if styles else 'varied'}."
    )


if __name__ == "__main__":
    mcp.run()
