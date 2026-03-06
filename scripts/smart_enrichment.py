"""
Smart enrichment pipeline: uses filename analysis, page type inference, 
and source-based heuristics to enrich screenshot patterns with metadata.
Then applies vision results (from data/vision_results.json) on top.
"""
import json
import re
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
PATTERNS_PATH = BASE_DIR / "data" / "patterns.json"
VISION_RESULTS_PATH = BASE_DIR / "data" / "vision_results.json"

# ============================================================
# Page type → expected UI elements mapping (from real design knowledge)
# ============================================================
PAGE_TYPE_ELEMENTS = {
    "Dashboard": ["Navigation Bar", "Sidebar", "Card", "Chart", "Stats", "Button", "Avatar", "Dropdown", "Data Table", "Badge"],
    "Landing Page": ["Navigation Bar", "Hero Section", "Button", "Card", "Footer", "Icon Grid", "Testimonials"],
    "Landing": ["Navigation Bar", "Hero Section", "Button", "Card", "Footer", "Icon Grid"],
    "E-commerce": ["Navigation Bar", "Card", "Search Bar", "Button", "Image Gallery", "Dropdown", "Badge", "Pagination", "Footer"],
    "Auth": ["Form", "Button", "Card"],
    "Login": ["Form", "Button", "Card"],
    "Signup": ["Form", "Button", "Card"],
    "Settings": ["Navigation Bar", "Sidebar", "Form", "Toggle", "Button", "Tabs", "Dropdown"],
    "Profile": ["Avatar", "Card", "Button", "Tabs", "Stats", "Badge"],
    "Blog": ["Navigation Bar", "Card", "Image Gallery", "Footer", "Pagination"],
    "Chat Interface": ["Avatar", "Card", "Button", "Form", "Search Bar"],
    "Chat": ["Avatar", "Card", "Button", "Form", "Search Bar"],
    "Portfolio": ["Navigation Bar", "Image Gallery", "Card", "Button", "Hero Section", "Footer"],
    "Admin Panel": ["Navigation Bar", "Sidebar", "Data Table", "Card", "Chart", "Button", "Badge", "Dropdown", "Search Bar"],
    "Analytics": ["Navigation Bar", "Sidebar", "Chart", "Card", "Stats", "Dropdown", "Data Table"],
    "Pricing": ["Navigation Bar", "Card", "Button", "Pricing Table", "Footer", "Icon Grid", "Toggle"],
    "Social Feed": ["Avatar", "Card", "Button", "Image Gallery", "Badge", "Search Bar"],
    "CRM": ["Navigation Bar", "Sidebar", "Data Table", "Card", "Button", "Chart", "Dropdown", "Avatar", "Badge"],
    "Calendar": ["Navigation Bar", "Calendar", "Button", "Card", "Dropdown"],
    "Kanban": ["Navigation Bar", "Card", "Button", "Dropdown", "Badge", "Avatar"],
    "Documentation": ["Navigation Bar", "Sidebar", "Search Bar", "Button", "Breadcrumb", "Tabs"],
    "Checkout": ["Form", "Button", "Card", "Progress Bar", "Stepper"],
    "Onboarding": ["Form", "Button", "Progress Bar", "Stepper", "Card"],
    "File Manager": ["Navigation Bar", "Sidebar", "Data Table", "Button", "Search Bar", "Breadcrumb", "Dropdown"],
    "Media Player": ["Button", "Progress Bar", "Card", "Image Gallery"],
    "Search Results": ["Navigation Bar", "Search Bar", "Card", "Pagination", "Dropdown", "Button"],
    "Product Page": ["Navigation Bar", "Button", "Image Gallery", "Card", "Badge", "Dropdown", "Tabs", "Footer"],
    "Product Listing": ["Navigation Bar", "Card", "Search Bar", "Dropdown", "Pagination", "Badge", "Button"],
    "Email": ["Navigation Bar", "Sidebar", "Card", "Button", "Badge", "Search Bar", "Avatar"],
    "Notifications": ["Card", "Badge", "Avatar", "Button", "Tabs"],
    "Weather": ["Card", "Chart", "Stats", "Icon Grid"],
    "Map": ["Navigation Bar", "Search Bar", "Card", "Button"],
    "Error Page": ["Button", "Hero Section"],
    "Empty State": ["Button", "Hero Section"],
    "Data Table": ["Navigation Bar", "Data Table", "Search Bar", "Button", "Dropdown", "Pagination"],
    "Project Management": ["Navigation Bar", "Sidebar", "Card", "Button", "Badge", "Avatar", "Dropdown", "Progress Bar"],
    "SaaS": ["Navigation Bar", "Hero Section", "Card", "Button", "Footer", "Pricing Table", "Testimonials"],
    "Agency": ["Navigation Bar", "Hero Section", "Image Gallery", "Card", "Button", "Footer"],
    "Corporate": ["Navigation Bar", "Hero Section", "Card", "Button", "Footer", "Stats", "Testimonials"],
    "Web App": ["Navigation Bar", "Sidebar", "Button", "Card", "Form"],
    "Mobile App": ["Navigation Bar", "Card", "Button", "Avatar"],
}

# Component hints for detected elements
COMPONENT_PROPS = {
    "Navigation Bar": {"name": "NavBar", "props": ["items", "activeItem", "logo", "onNavigate"]},
    "Sidebar": {"name": "Sidebar", "props": ["items", "collapsed", "activeItem", "onToggle"]},
    "Search Bar": {"name": "SearchInput", "props": ["placeholder", "value", "onChange", "onSubmit"]},
    "Button": {"name": "Button", "props": ["variant", "size", "onClick", "disabled", "loading"]},
    "Card": {"name": "Card", "props": ["title", "description", "image", "actions", "footer"]},
    "Data Table": {"name": "DataTable", "props": ["columns", "data", "sortable", "filterable", "pagination"]},
    "Form": {"name": "FormField", "props": ["label", "type", "placeholder", "value", "onChange", "error"]},
    "Dropdown": {"name": "Select", "props": ["options", "value", "onChange", "placeholder"]},
    "Modal": {"name": "Dialog", "props": ["open", "onClose", "title", "description"]},
    "Tabs": {"name": "Tabs", "props": ["items", "activeTab", "onChange", "variant"]},
    "Chart": {"name": "Chart", "props": ["type", "data", "options", "responsive"]},
    "Avatar": {"name": "Avatar", "props": ["src", "alt", "size", "fallback"]},
    "Badge": {"name": "Badge", "props": ["count", "variant", "dot"]},
    "Progress Bar": {"name": "Progress", "props": ["value", "max", "label"]},
    "Hero Section": {"name": "Hero", "props": ["title", "subtitle", "cta", "background"]},
    "Footer": {"name": "Footer", "props": ["links", "copyright", "social"]},
    "Pricing Table": {"name": "PricingCard", "props": ["plan", "price", "features", "cta", "popular"]},
    "Image Gallery": {"name": "Gallery", "props": ["images", "columns", "lightbox"]},
    "Testimonials": {"name": "Testimonial", "props": ["quote", "author", "role", "avatar"]},
    "Stats": {"name": "StatCard", "props": ["label", "value", "change", "trend"]},
    "Timeline": {"name": "Timeline", "props": ["items", "orientation"]},
    "Toggle": {"name": "Switch", "props": ["checked", "onChange", "label"]},
    "Icon Grid": {"name": "FeatureGrid", "props": ["items", "columns", "iconSize"]},
    "Calendar": {"name": "Calendar", "props": ["selected", "onSelect", "events", "view"]},
    "Stepper": {"name": "Stepper", "props": ["steps", "activeStep", "onStepClick"]},
    "Pagination": {"name": "Pagination", "props": ["total", "current", "onChange", "pageSize"]},
    "Breadcrumb": {"name": "Breadcrumb", "props": ["items", "separator"]},
    "Toast": {"name": "Toast", "props": ["message", "type", "duration", "action"]},
    "Accordion": {"name": "Accordion", "props": ["items", "multiple", "defaultOpen"]},
    "Tooltip": {"name": "Tooltip", "props": ["content", "trigger", "position"]},
    "Tag Chips": {"name": "Tag", "props": ["label", "variant", "removable"]},
    "File Upload": {"name": "FileUpload", "props": ["accept", "maxSize", "multiple", "onUpload"]},
    "Video Player": {"name": "VideoPlayer", "props": ["src", "poster", "controls", "autoplay"]},
}

# Filename keywords → page type inference
FILENAME_PAGE_HINTS = {
    "dashboard": "Dashboard",
    "admin": "Admin Panel",
    "analytics": "Analytics",
    "chart": "Analytics",
    "login": "Auth",
    "signin": "Auth",
    "signup": "Auth",
    "register": "Auth",
    "auth": "Auth",
    "pricing": "Pricing",
    "checkout": "Checkout",
    "cart": "E-commerce",
    "shop": "E-commerce",
    "store": "E-commerce",
    "product": "E-commerce",
    "ecommerce": "E-commerce",
    "e-commerce": "E-commerce",
    "profile": "Profile",
    "account": "Profile",
    "settings": "Settings",
    "preference": "Settings",
    "blog": "Blog",
    "article": "Blog",
    "post": "Blog",
    "chat": "Chat",
    "message": "Chat",
    "messenger": "Chat",
    "inbox": "Email",
    "email": "Email",
    "mail": "Email",
    "calendar": "Calendar",
    "schedule": "Calendar",
    "kanban": "Kanban",
    "board": "Kanban",
    "task": "Project Management",
    "project": "Project Management",
    "portfolio": "Portfolio",
    "studio": "Portfolio",
    "agency": "Agency",
    "folio": "Portfolio",
    "landing": "Landing Page",
    "homepage": "Landing Page",
    "home": "Landing Page",
    "hero": "Landing Page",
    "saas": "SaaS",
    "crm": "CRM",
    "crypto": "Dashboard",
    "finance": "Dashboard",
    "banking": "Dashboard",
    "wallet": "Dashboard",
    "social": "Social Feed",
    "feed": "Social Feed",
    "doc": "Documentation",
    "docs": "Documentation",
    "file-manager": "File Manager",
    "weather": "Weather",
    "map": "Map",
    "music": "Media Player",
    "player": "Media Player",
    "video": "Media Player",
    "search": "Search Results",
    "onboarding": "Onboarding",
    "wizard": "Onboarding",
    "notification": "Notifications",
    "error": "Error Page",
    "404": "Error Page",
    "empty": "Empty State",
    "table": "Data Table",
}

# Filename keywords → visual style inference
FILENAME_STYLE_HINTS = {
    "dark": "Dark",
    "light": "Light",
    "minimal": "Minimal",
    "clean": "Minimal",
    "bold": "Bold",
    "colorful": "Bold",
    "gradient": "Gradient",
    "glass": "Glassmorphism",
    "neon": "Futuristic",
    "futuristic": "Futuristic",
    "retro": "Retro",
    "vintage": "Retro",
    "luxury": "Premium",
    "premium": "Premium",
    "elegant": "Premium",
    "corporate": "Corporate",
    "business": "Corporate",
    "creative": "Playful",
    "fun": "Playful",
    "3d": "3D",
}

# Source-based quality adjustments
SOURCE_QUALITY = {
    "curated": 8.0,
    "awwwards": 7.5,
    "dribbble": 7.0,
    "landbook": 5.5,
}


def infer_page_type_from_name(name):
    """Infer page type from pattern name/filename."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")
    
    for keyword, page_type in FILENAME_PAGE_HINTS.items():
        if keyword in name_lower:
            return page_type
    
    return None


def infer_visual_styles_from_name(name):
    """Infer visual styles from pattern name."""
    name_lower = name.lower().replace("_", " ").replace("-", " ")
    styles = []
    
    for keyword, style in FILENAME_STYLE_HINTS.items():
        if keyword in name_lower:
            styles.append(style)
    
    return styles[:4]


def infer_color_mode(name, source):
    """Infer color mode from name hints."""
    name_lower = name.lower()
    if "dark" in name_lower:
        return "dark"
    elif "light" in name_lower or "white" in name_lower:
        return "light"
    return None  # Unknown


def enrich_patterns():
    """Main enrichment pipeline."""
    with open(PATTERNS_PATH) as f:
        patterns = json.load(f)
    
    # Load any vision results
    vision_results = {}
    if VISION_RESULTS_PATH.exists():
        with open(VISION_RESULTS_PATH) as f:
            vision_results = json.load(f)
        print(f"Loaded {len(vision_results)} vision results")
    
    screenshot_patterns = [
        (i, p) for i, p in enumerate(patterns)
        if p["id"].startswith("screenshot-")
    ]
    
    enriched_heuristic = 0
    enriched_vision = 0
    
    for idx, (pattern_idx, pattern) in enumerate(screenshot_patterns):
        image_url = pattern.get("image_url", "")
        name = pattern.get("name", "")
        source = pattern.get("source", "")
        
        # ---- Vision results (highest priority) ----
        if image_url in vision_results:
            vr = vision_results[image_url]
            if vr.get("ui_elements"):
                patterns[pattern_idx]["ui_elements"] = vr["ui_elements"]
            if vr.get("visual_style"):
                patterns[pattern_idx]["visual_style"] = vr["visual_style"]
            if vr.get("page_type"):
                patterns[pattern_idx]["page_type"] = vr["page_type"]
            if vr.get("layout_type"):
                patterns[pattern_idx]["layout_type"] = vr["layout_type"]
            if vr.get("color_mode"):
                patterns[pattern_idx]["color_mode"] = vr["color_mode"]
            if vr.get("quality_score"):
                patterns[pattern_idx]["quality_score"] = float(vr["quality_score"])
            
            # Generate component hints
            hints = [COMPONENT_PROPS[el] for el in vr.get("ui_elements", [])[:8] if el in COMPONENT_PROPS]
            if hints:
                patterns[pattern_idx]["component_hints"] = hints
            
            tags = patterns[pattern_idx].get("tags", [])
            if "vision-enriched" not in tags:
                tags.append("vision-enriched")
            patterns[pattern_idx]["tags"] = tags
            
            enriched_vision += 1
            continue
        
        # ---- Heuristic enrichment (for non-vision patterns) ----
        needs_enrichment = not pattern.get("ui_elements")
        
        if not needs_enrichment:
            continue
        
        # Infer page type
        current_page = patterns[pattern_idx].get("page_type", "")
        inferred_page = infer_page_type_from_name(name)
        
        if inferred_page and (not current_page or current_page in ("Unknown", "Web Page", "Screenshot", "")):
            patterns[pattern_idx]["page_type"] = inferred_page
        
        # Use page type (existing or inferred) to populate UI elements
        effective_page = patterns[pattern_idx].get("page_type", "")
        if effective_page in PAGE_TYPE_ELEMENTS:
            patterns[pattern_idx]["ui_elements"] = PAGE_TYPE_ELEMENTS[effective_page]
        elif effective_page:
            # Try partial match
            for key, elements in PAGE_TYPE_ELEMENTS.items():
                if key.lower() in effective_page.lower() or effective_page.lower() in key.lower():
                    patterns[pattern_idx]["ui_elements"] = elements
                    break
        
        # If still no elements, assign defaults based on source
        if not patterns[pattern_idx].get("ui_elements"):
            if source == "dribbble":
                # Dribbble tends to be app UI designs
                patterns[pattern_idx]["ui_elements"] = ["Card", "Button", "Navigation Bar"]
            elif source == "awwwards":
                # Awwwards tends to be landing pages and portfolios
                patterns[pattern_idx]["ui_elements"] = ["Navigation Bar", "Hero Section", "Button", "Footer"]
            elif source == "landbook":
                # Landbook is landing pages
                patterns[pattern_idx]["ui_elements"] = ["Navigation Bar", "Hero Section", "Button", "Card", "Footer"]
            else:
                patterns[pattern_idx]["ui_elements"] = ["Button", "Card"]
        
        # Visual styles from name
        styles = infer_visual_styles_from_name(name)
        if not patterns[pattern_idx].get("visual_style"):
            if styles:
                patterns[pattern_idx]["visual_style"] = styles
            elif source == "awwwards":
                patterns[pattern_idx]["visual_style"] = ["Premium"]
            elif source == "dribbble":
                patterns[pattern_idx]["visual_style"] = ["Bold"]
        
        # Color mode
        if not patterns[pattern_idx].get("color_mode"):
            cm = infer_color_mode(name, source)
            if cm:
                patterns[pattern_idx]["color_mode"] = cm
        
        # Layout type inference from page type
        if not patterns[pattern_idx].get("layout_type"):
            page = patterns[pattern_idx].get("page_type", "")
            layout_map = {
                "Dashboard": "sidebar_detail",
                "Admin Panel": "sidebar_detail",
                "Analytics": "sidebar_detail",
                "CRM": "sidebar_detail",
                "Settings": "sidebar_detail",
                "Email": "sidebar_detail",
                "File Manager": "sidebar_detail",
                "Landing Page": "full_bleed",
                "Landing": "full_bleed",
                "SaaS": "full_bleed",
                "Portfolio": "full_bleed",
                "Agency": "full_bleed",
                "Corporate": "full_bleed",
                "Auth": "single_column",
                "Login": "single_column",
                "Signup": "single_column",
                "Blog": "single_column",
                "Checkout": "single_column",
                "E-commerce": "card_grid",
                "Product Listing": "card_grid",
                "Social Feed": "single_column",
                "Chat": "split_screen",
                "Kanban": "dashboard_panels",
                "Project Management": "dashboard_panels",
            }
            if page in layout_map:
                patterns[pattern_idx]["layout_type"] = layout_map[page]
        
        # Component hints
        elements = patterns[pattern_idx].get("ui_elements", [])
        hints = [COMPONENT_PROPS[el] for el in elements[:8] if el in COMPONENT_PROPS]
        if hints:
            patterns[pattern_idx]["component_hints"] = hints
        
        # Quality score based on source + metadata richness
        base_quality = SOURCE_QUALITY.get(source, 5.0)
        element_bonus = min(1.5, len(patterns[pattern_idx].get("ui_elements", [])) * 0.1)
        style_bonus = min(0.5, len(patterns[pattern_idx].get("visual_style", [])) * 0.15)
        patterns[pattern_idx]["quality_score"] = round(min(10.0, base_quality + element_bonus + style_bonus), 1)
        
        # Tag as enriched
        tags = patterns[pattern_idx].get("tags", [])
        if "heuristic-enriched" not in tags:
            tags.append("heuristic-enriched")
        patterns[pattern_idx]["tags"] = tags
        
        enriched_heuristic += 1
    
    # Sort by quality
    patterns.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
    
    # Save
    with open(PATTERNS_PATH, "w") as f:
        json.dump(patterns, f, indent=2)
    
    # ============================================================
    # STATS
    # ============================================================
    print(f"\n{'='*60}")
    print(f"ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    print(f"  Vision-enriched: {enriched_vision}")
    print(f"  Heuristic-enriched: {enriched_heuristic}")
    print(f"  Total patterns: {len(patterns)}")
    
    # Check coverage
    has_elements = sum(1 for p in patterns if p.get("ui_elements"))
    has_hints = sum(1 for p in patterns if p.get("component_hints"))
    has_style = sum(1 for p in patterns if p.get("visual_style"))
    has_layout = sum(1 for p in patterns if p.get("layout_type"))
    
    print(f"\n  Coverage:")
    print(f"    Has ui_elements: {has_elements}/{len(patterns)}")
    print(f"    Has component_hints: {has_hints}/{len(patterns)}")
    print(f"    Has visual_style: {has_style}/{len(patterns)}")
    print(f"    Has layout_type: {has_layout}/{len(patterns)}")
    
    # Element distribution
    all_elements = Counter()
    for p in patterns:
        for el in p.get("ui_elements", []):
            all_elements[el] += 1
    
    print(f"\n  Top UI elements:")
    for elem, count in all_elements.most_common(15):
        print(f"    {elem}: {count}")
    
    # Page type distribution
    all_pages = Counter()
    for p in patterns:
        pt = p.get("page_type")
        if pt:
            all_pages[pt] += 1
    
    print(f"\n  Page types:")
    for page, count in all_pages.most_common(15):
        print(f"    {page}: {count}")
    
    # Quality distribution
    quality_bins = Counter()
    for p in patterns:
        q = p.get("quality_score", 0)
        if q >= 9:
            quality_bins["9-10 (excellent)"] += 1
        elif q >= 7:
            quality_bins["7-8 (good)"] += 1
        elif q >= 5:
            quality_bins["5-6 (average)"] += 1
        else:
            quality_bins["0-4 (low)"] += 1
    
    print(f"\n  Quality distribution:")
    for bucket in ["9-10 (excellent)", "7-8 (good)", "5-6 (average)", "0-4 (low)"]:
        print(f"    {bucket}: {quality_bins.get(bucket, 0)}")


if __name__ == "__main__":
    enrich_patterns()
