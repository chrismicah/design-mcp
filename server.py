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

        # Get library recommendations based on component type
        recommended_libraries = []
        try:
            libs_data = _load_libraries()
            element_map = libs_data["mapping_rules"]["ui_element_to_library"]
            if component_type in element_map:
                lib_ids = element_map[component_type][:3]
                for lib_id in lib_ids:
                    for lib in libs_data["libraries"]:
                        if lib["id"] == lib_id:
                            recommended_libraries.append({
                                "name": lib["name"],
                                "install": lib["install"],
                                "reason": f"Has a production-ready {component_type} component",
                                "example": lib.get("example", ""),
                            })
                            break
        except Exception:
            pass

        return {
            "anti_patterns_found": anti_patterns_found,
            "recommended_layout": recommended_layout,
            "semantic_tokens_to_apply": semantic_tokens_to_apply,
            "suggested_component_structure": suggested_component_structure,
            "severity_summary": severity_summary,
            "refactoring_suggestions": refactoring_suggestions,
            "recommended_libraries": recommended_libraries,
            "detected_component_type": component_type,
        }

    except Exception:
        return {
            "anti_patterns_found": [],
            "recommended_layout": {},
            "semantic_tokens_to_apply": {},
            "suggested_component_structure": [],
            "severity_summary": {"errors": 0, "warnings": 0, "info": 0},
            "refactoring_suggestions": [],
            "recommended_libraries": [],
            "detected_component_type": "Unknown",
        }


# ============================================================
# TOOL 8: Get Library Recommendations
# ============================================================
@mcp.tool()
async def get_library_recommendations(
    use_case: Optional[str] = None,
    ui_elements: Optional[list[str]] = None,
    visual_style: Optional[str] = None,
    needs_animation: bool = False,
    needs_3d: bool = False,
    needs_charts: bool = False,
) -> dict:
    """
    Get recommended frontend libraries based on your project needs.
    Maps use cases, UI elements, visual styles, and feature requirements
    to the best React libraries (Shadcn, Radix, Mantine, React Bits, etc.).

    Args:
        use_case: What you're building (e.g. 'dashboard', 'landing_page', 'creative_portfolio', 'saas_product', 'ecommerce')
        ui_elements: UI elements you need (e.g. ['Button', 'Modal', 'Data Table', 'Carousel'])
        visual_style: Target visual style (e.g. 'Minimal', 'Glassmorphism', 'Futuristic', 'Playful')
        needs_animation: Whether you need animations/transitions
        needs_3d: Whether you need 3D elements
        needs_charts: Whether you need data visualization/charts

    Returns:
        Recommended libraries with install commands, code examples, and reasoning.
    """
    try:
        libs_data = _load_libraries()
        libraries = {lib["id"]: lib for lib in libs_data["libraries"]}
        mapping = libs_data["mapping_rules"]

        recommended_ids = set()
        recommendations = []

        # Map use case to libraries
        if use_case:
            use_case_key = use_case.lower().replace(" ", "_").replace("-", "_")
            if use_case_key in mapping["use_case_to_library"]:
                for lib_id in mapping["use_case_to_library"][use_case_key]:
                    recommended_ids.add(lib_id)

        # Map UI elements to libraries
        if ui_elements:
            element_map = mapping["ui_element_to_library"]
            for element in ui_elements:
                if element in element_map:
                    for lib_id in element_map[element][:3]:  # Top 3 per element
                        recommended_ids.add(lib_id)

        # Map visual style to libraries
        if visual_style and visual_style in mapping.get("visual_style_to_library", {}):
            for lib_id in mapping["visual_style_to_library"][visual_style]:
                recommended_ids.add(lib_id)

        # Add based on feature flags
        if needs_animation:
            recommended_ids.update(["framer-motion", "gsap", "react-bits"])
        if needs_3d:
            recommended_ids.update(["three-js", "react-bits"])
        if needs_charts:
            recommended_ids.update(["recharts", "d3-js"])

        # If nothing matched, return the premium stack
        if not recommended_ids:
            recommended_ids = set(mapping["premium_stack"]["core"])

        # Build recommendation objects
        for lib_id in recommended_ids:
            if lib_id in libraries:
                lib = libraries[lib_id]
                recommendations.append({
                    "name": lib["name"],
                    "category": lib["category"],
                    "description": lib["description"],
                    "install": lib["install"],
                    "docs": lib["docs_url"],
                    "when_to_use": lib["when_to_use"],
                    "example": lib.get("example", ""),
                })

        # Sort: ui_components first, then by category
        category_order = {"ui_components": 0, "styling": 1, "animation": 2, "creative_components": 3, "3d": 4, "utility": 5}
        recommendations.sort(key=lambda r: category_order.get(r["category"], 99))

        # Also search our patterns DB for matching examples
        pattern_examples = []
        if use_case:
            results = db.search(query=use_case, limit=3)
            for r in results:
                pattern_examples.append({
                    "name": r.name,
                    "page_type": r.page_type,
                    "layout_type": r.layout_type.value if r.layout_type else None,
                    "visual_style": r.visual_style,
                })

        return {
            "recommendations": recommendations,
            "premium_stack": mapping["premium_stack"],
            "matching_design_patterns": pattern_examples,
            "total_libraries": len(recommendations),
        }

    except Exception:
        return {
            "recommendations": [],
            "premium_stack": {"core": ["tailwind-css", "shadcn-ui", "framer-motion"]},
            "matching_design_patterns": [],
            "total_libraries": 0,
        }


# ============================================================
# TOOL 9: Get Library Details
# ============================================================
@mcp.tool()
async def get_library_details(library_name: str) -> dict:
    """
    Get detailed information about a specific frontend library including
    all available components, install command, code examples, and what it pairs with.

    Args:
        library_name: Library name or ID (e.g. 'shadcn', 'react-bits', 'framer-motion', 'mantine')

    Returns:
        Full library details with components list, examples, and pairing suggestions.
    """
    try:
        libs_data = _load_libraries()
        name_lower = library_name.lower().replace(" ", "-").replace("/", "-")

        for lib in libs_data["libraries"]:
            if (name_lower in lib["id"].lower() or
                name_lower in lib["name"].lower() or
                name_lower.replace("-", "") in lib["name"].lower().replace(" ", "").replace("/", "")):
                return {
                    "library": lib,
                    "pairs_with": [
                        {"id": pid, "name": next((l["name"] for l in libs_data["libraries"] if l["id"] == pid), pid)}
                        for pid in lib.get("pairs_with", [])
                    ],
                }

        # Fuzzy match
        matches = []
        for lib in libs_data["libraries"]:
            searchable = f"{lib['id']} {lib['name']} {lib['description']}".lower()
            if any(word in searchable for word in name_lower.split("-")):
                matches.append(lib["name"])

        return {
            "error": f"Library '{library_name}' not found",
            "did_you_mean": matches[:5],
            "available": [lib["name"] for lib in libs_data["libraries"]],
        }

    except Exception:
        return {"error": f"Could not load library data for '{library_name}'"}


# ============================================================
# TOOL 10: Scan Project for Anti-Patterns
# ============================================================
@mcp.tool()
async def scan_project(
    project_path: str,
    file_extensions: Optional[list[str]] = None,
    max_files: int = 50,
) -> dict:
    """
    Scan an entire project directory for UI anti-patterns across all component files.
    Returns a prioritized report of issues found in each file with fix suggestions.
    Use this when someone says "make my app look professional" or "refactor my whole site".

    Args:
        project_path: Absolute path to the project directory (e.g. 'C:/Users/me/Projects/my-app/src')
        file_extensions: File types to scan (default: ['.jsx', '.tsx', '.js', '.ts', '.html', '.vue', '.svelte'])
        max_files: Maximum files to analyze (default 50, to keep response manageable)

    Returns:
        Project-wide analysis with per-file findings, overall health score,
        priority fix list, and recommended libraries for the whole project.
    """
    try:
        project = Path(project_path)
        if not project.exists():
            return {"error": f"Path not found: {project_path}"}
        
        extensions = file_extensions or ['.jsx', '.tsx', '.js', '.ts', '.html', '.vue', '.svelte']
        
        # Find all UI component files
        ui_files = []
        for ext in extensions:
            if project.is_file():
                if project.suffix in extensions:
                    ui_files.append(project)
            else:
                ui_files.extend(project.rglob(f"*{ext}"))
        
        # Filter out node_modules, dist, build, .next, etc.
        skip_dirs = {'node_modules', '.next', 'dist', 'build', '.git', '__pycache__', '.venv', 'coverage'}
        ui_files = [
            f for f in ui_files 
            if not any(skip in f.parts for skip in skip_dirs)
        ]
        
        # Limit
        ui_files = sorted(ui_files)[:max_files]
        
        if not ui_files:
            return {
                "error": "No UI component files found",
                "searched_path": str(project),
                "extensions": extensions,
                "suggestion": "Try pointing to your src/ or components/ directory"
            }
        
        # Analyze each file
        file_reports = []
        all_findings = []
        component_types_seen = set()
        total_severity = {"errors": 0, "warnings": 0, "info": 0}
        
        for filepath in ui_files:
            try:
                code = filepath.read_text(encoding='utf-8', errors='ignore')
                if len(code) < 20:  # Skip near-empty files
                    continue
                
                analysis = analyze_code(code)
                
                if analysis["findings"]:
                    relative_path = str(filepath.relative_to(project)) if filepath.is_relative_to(project) else str(filepath)
                    
                    file_report = {
                        "file": relative_path,
                        "component_type": analysis["component_type"],
                        "issues_count": len(analysis["findings"]),
                        "severity": analysis["severity_summary"],
                        "findings": [
                            {
                                "type": f["type"],
                                "severity": f["severity"],
                                "message": f["message"],
                                "line": f["line"],
                                "suggestion": f["suggestion"],
                            }
                            for f in analysis["findings"]
                        ],
                    }
                    file_reports.append(file_report)
                    all_findings.extend(analysis["findings"])
                    component_types_seen.add(analysis["component_type"])
                    
                    total_severity["errors"] += analysis["severity_summary"]["errors"]
                    total_severity["warnings"] += analysis["severity_summary"]["warnings"]
                    total_severity["info"] += analysis["severity_summary"]["info"]
                    
            except Exception:
                continue
        
        # Sort files by severity (errors first, then by issue count)
        file_reports.sort(key=lambda r: (
            -r["severity"]["errors"],
            -r["severity"]["warnings"],
            -r["issues_count"]
        ))
        
        # Calculate health score (0-100, higher is better)
        total_issues = len(all_findings)
        files_scanned = len(ui_files)
        if files_scanned == 0:
            health_score = 100
        else:
            error_penalty = total_severity["errors"] * 5
            warning_penalty = total_severity["warnings"] * 2
            info_penalty = total_severity["info"] * 0.5
            raw_score = max(0, 100 - error_penalty - warning_penalty - info_penalty)
            health_score = round(raw_score, 1)
        
        # Aggregate anti-pattern types across project
        from collections import Counter
        pattern_counts = Counter(f["type"] for f in all_findings)
        top_issues = [
            {"type": ptype, "count": count}
            for ptype, count in pattern_counts.most_common(10)
        ]
        
        # Build priority fix list (top 5 most impactful fixes)
        priority_fixes = []
        seen_fix_types = set()
        for report in file_reports:
            for finding in report["findings"]:
                if finding["severity"] == "error" and finding["type"] not in seen_fix_types:
                    priority_fixes.append({
                        "file": report["file"],
                        "issue": finding["message"],
                        "fix": finding["suggestion"],
                        "severity": "error",
                    })
                    seen_fix_types.add(finding["type"])
                if len(priority_fixes) >= 10:
                    break
            if len(priority_fixes) >= 10:
                break
        
        # Recommend libraries for the whole project
        all_elements = list(component_types_seen)
        project_libs = []
        try:
            libs_data = _load_libraries()
            element_map = libs_data["mapping_rules"]["ui_element_to_library"]
            lib_scores = Counter()
            for comp_type in all_elements:
                if comp_type in element_map:
                    for lib_id in element_map[comp_type]:
                        lib_scores[lib_id] += 1
            
            for lib_id, score in lib_scores.most_common(5):
                for lib in libs_data["libraries"]:
                    if lib["id"] == lib_id:
                        project_libs.append({
                            "name": lib["name"],
                            "install": lib["install"],
                            "relevance": f"Covers {score} component types in your project",
                        })
                        break
        except Exception:
            pass
        
        return {
            "project_health_score": health_score,
            "files_scanned": files_scanned,
            "files_with_issues": len(file_reports),
            "total_issues": total_issues,
            "severity_summary": total_severity,
            "top_issues": top_issues,
            "priority_fixes": priority_fixes,
            "recommended_libraries": project_libs,
            "file_reports": file_reports[:20],  # Top 20 worst files
            "component_types_found": list(component_types_seen),
        }
    
    except Exception as e:
        return {"error": f"Failed to scan project: {str(e)}"}


# ============================================================
# TOOL 11: Generate Refactored Code
# ============================================================
@mcp.tool()
async def generate_refactored_code(
    source_code: str,
    target_library: str = "shadcn-ui",
    include_imports: bool = True,
) -> dict:
    """
    Takes vibecoded source code and generates a refactoring plan with
    concrete code suggestions using the specified component library.
    
    This tool analyzes the code, identifies what it's trying to be,
    finds matching design patterns in our database, and produces
    specific code transformations mapped to real library components.

    Args:
        source_code: The raw UI code to refactor (JSX/TSX/HTML)
        target_library: Which library to use for refactoring (default: 'shadcn-ui')
            Options: 'shadcn-ui', 'mantine', 'chakra-ui', 'nextui', 'radix-ui'
        include_imports: Whether to include import statements in suggestions

    Returns:
        Refactoring plan with before/after code mappings, import statements,
        and step-by-step transformation instructions.
    """
    try:
        # Analyze the code
        analysis = analyze_code(source_code)
        findings = analysis["findings"]
        component_type = analysis["component_type"]
        
        # Load library data
        libs_data = _load_libraries()
        target_lib = None
        for lib in libs_data["libraries"]:
            if target_library.lower().replace(" ", "-") in lib["id"]:
                target_lib = lib
                break
        
        if not target_lib:
            target_lib = next((l for l in libs_data["libraries"] if l["id"] == "shadcn-ui"), None)
        
        # Search for matching design patterns
        pattern_results = db.search(query=component_type, limit=3)
        design_reference = []
        for p in pattern_results:
            ref = {"name": p.name, "page_type": p.page_type}
            if p.layout_type:
                ref["layout_type"] = p.layout_type.value
            if p.layout_notes:
                ref["layout_notes"] = p.layout_notes
            if p.semantic_tokens:
                ref["semantic_tokens"] = p.semantic_tokens
            if p.component_hints:
                ref["component_hints"] = p.component_hints
            design_reference.append(ref)
        
        # Get semantic tokens
        tokens_path = BASE_DIR / "data" / "tokens" / "semantic_tokens.json"
        semantic_tokens = {}
        try:
            with open(tokens_path) as f:
                semantic_tokens = json.load(f)
        except Exception:
            pass
        
        # Build transformation instructions
        transformations = []
        imports_needed = set()
        
        # Map anti-patterns to specific transformations
        for finding in findings:
            transform = {
                "issue": finding["message"],
                "severity": finding["severity"],
            }
            
            ftype = finding["type"]
            
            if ftype == "interactive_div" and target_lib:
                if "Button" in target_lib.get("components", []):
                    transform["fix"] = f"Replace <div onClick={{...}}> with <Button> from {target_lib['name']}"
                    transform["code_hint"] = f'<Button onClick={{handler}} variant="default">Text</Button>'
                    imports_needed.add(f"import {{ Button }} from '{_get_import_path(target_lib)}/button'")
                elif component_type == "Dropdown" and "Select" in target_lib.get("components", []):
                    transform["fix"] = f"Replace custom dropdown with <Select> from {target_lib['name']}"
                    transform["code_hint"] = '<Select onValueChange={handler}>\n  <SelectTrigger><SelectValue /></SelectTrigger>\n  <SelectContent>\n    <SelectItem value="opt">Option</SelectItem>\n  </SelectContent>\n</Select>'
                    imports_needed.add(f"import {{ Select, SelectContent, SelectItem, SelectTrigger, SelectValue }} from '{_get_import_path(target_lib)}/select'")
            
            elif ftype == "magic_hex_color":
                transform["fix"] = "Replace hardcoded hex with semantic color token"
                transform["code_hint"] = "bg-primary, text-foreground, border-input, text-muted-foreground"
            
            elif ftype == "hardcoded_pixels":
                transform["fix"] = "Replace pixel values with Tailwind scale or responsive units"
                transform["code_hint"] = "w-full sm:w-auto, p-4, h-12, rounded-lg (use scale values)"
            
            elif ftype == "inline_style_abuse":
                transform["fix"] = "Move inline styles to Tailwind utility classes"
                transform["code_hint"] = "shadow-sm, rounded-lg, etc. (extract each style to a utility)"
            
            elif ftype == "absolute_positioning":
                transform["fix"] = "Replace absolute positioning with flexbox or grid"
                transform["code_hint"] = "flex items-center justify-between gap-4"
            
            elif ftype == "margin_alignment_hack":
                transform["fix"] = "Replace large margins with flexbox distribution"
                transform["code_hint"] = "ml-auto (push right), flex justify-between, gap-4"
            
            elif ftype == "div_soup":
                transform["fix"] = "Replace generic divs with semantic HTML5 elements"
                transform["code_hint"] = "<main>, <section>, <article>, <nav>, <header>, <footer>, <aside>"
            
            elif ftype == "missing_aria":
                transform["fix"] = "Add ARIA attributes for screen reader support"
                transform["code_hint"] = 'aria-expanded={isOpen}, role="dialog", aria-modal="true"'
            
            elif ftype == "missing_focus_states":
                transform["fix"] = "Add visible focus indicators"
                transform["code_hint"] = "focus:ring-2 focus:ring-ring focus:ring-offset-2"
            
            elif ftype == "unlabeled_input":
                transform["fix"] = "Add label or aria-label to input"
                transform["code_hint"] = '<Label htmlFor="field-id">Field Name</Label>\n<Input id="field-id" />'
                if target_lib and "Input" in target_lib.get("components", []):
                    imports_needed.add(f"import {{ Input }} from '{_get_import_path(target_lib)}/input'")
                    imports_needed.add(f"import {{ Label }} from '{_get_import_path(target_lib)}/label'")
            
            elif ftype == "zindex_abuse":
                transform["fix"] = "Remove forced z-index, fix DOM structure instead"
                transform["code_hint"] = "Use z-10 or z-20 max; use portals for overlays"
            
            elif ftype == "fixed_viewport_height":
                transform["fix"] = "Use dynamic viewport height"
                transform["code_hint"] = "min-h-screen or h-dvh instead of h-[100vh]"
            
            else:
                transform["fix"] = finding["suggestion"]
                transform["code_hint"] = ""
            
            transformations.append(transform)
        
        # Component-specific suggestions
        component_suggestion = {}
        if component_type != "Component" and target_lib:
            components = target_lib.get("components", [])
            if component_type in components:
                component_suggestion = {
                    "detected_as": component_type,
                    "library_component": f"{target_lib['name']} <{component_type}>",
                    "install": target_lib["install"],
                    "docs": target_lib["docs_url"],
                }
            # Map common types to library components
            component_map = {
                "Button": "Button",
                "Card": "Card",
                "Dropdown": "Select",
                "Modal": "Dialog",
                "Form": "Form",
                "Input": "Input",
                "Navigation Bar": "NavigationMenu",
                "Tabs": "Tabs",
                "Data Table": "Table",
                "Accordion": "Accordion",
                "Toast": "Toast",
                "Tooltip": "Tooltip",
            }
            mapped = component_map.get(component_type)
            if mapped and mapped in components:
                component_suggestion["use_component"] = mapped
                imports_needed.add(f"import {{ {mapped} }} from '{_get_import_path(target_lib)}/{mapped.lower()}'")
        
        return {
            "detected_component_type": component_type,
            "total_issues": len(findings),
            "severity_summary": analysis["severity_summary"],
            "target_library": target_lib["name"] if target_lib else "none",
            "imports_needed": sorted(imports_needed) if include_imports else [],
            "transformations": transformations,
            "component_suggestion": component_suggestion,
            "design_reference": design_reference,
            "semantic_tokens": {
                "colors": {
                    "primary": "hsl(var(--primary))",
                    "secondary": "hsl(var(--secondary))",
                    "destructive": "hsl(var(--destructive))",
                    "muted": "hsl(var(--muted))",
                    "accent": "hsl(var(--accent))",
                    "background": "hsl(var(--background))",
                    "foreground": "hsl(var(--foreground))",
                    "border": "hsl(var(--border))",
                    "input": "hsl(var(--input))",
                    "ring": "hsl(var(--ring))",
                },
                "note": "Use these CSS variable-based tokens instead of hardcoded hex values"
            },
        }
    
    except Exception as e:
        return {"error": f"Failed to generate refactoring plan: {str(e)}"}


def _get_import_path(lib: dict) -> str:
    """Get the import path for a library's components."""
    lib_id = lib.get("id", "")
    if lib_id == "shadcn-ui":
        return "@/components/ui"
    elif lib_id == "mantine":
        return "@mantine/core"
    elif lib_id == "chakra-ui":
        return "@chakra-ui/react"
    elif lib_id == "nextui":
        return "@nextui-org/react"
    elif lib_id == "radix-ui":
        return "@radix-ui/react"
    return lib.get("package", lib_id)


# ============================================================
# Helper Functions
# ============================================================

def _load_libraries() -> dict:
    """Load the libraries reference database."""
    libs_path = BASE_DIR / "data" / "libraries.json"
    with open(libs_path) as f:
        return json.load(f)

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
