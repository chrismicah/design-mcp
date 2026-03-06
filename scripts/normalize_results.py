"""Normalize free-form vision results to match our constrained schema."""
import json
from pathlib import Path

VALID_ELEMENTS = {"Navigation Bar","Sidebar","Card","Chart","Button","Data Table","Form","Avatar","Badge","Tabs","Modal","Search Bar","Toggle","Stats","Hero Section","Dropdown","Footer","Pricing Table","Image Gallery","Testimonials","Icon Grid","Timeline","Progress Bar","Tag Chips","Stepper","Calendar","File Upload","Video Player","Tooltip","Toast","Accordion","Breadcrumb","Pagination"}

VALID_STYLES = {"Minimal","Bold","Glassmorphism","Gradient","Corporate","Playful","Premium","Futuristic","Flat","3D","Dark","Editorial","Organic","Retro","Geometric"}

VALID_PAGES = {"Dashboard","Landing Page","E-commerce","Auth","Settings","Profile","Blog","Chat","Portfolio","Admin Panel","Analytics","Pricing","Social Feed","CRM","Calendar","Kanban","Documentation","Checkout","Onboarding","File Manager","Media Player","Search Results","Agency","Corporate","SaaS"}

VALID_LAYOUTS = {"sidebar_detail","single_column","split_screen","card_grid","full_bleed","dashboard_panels","masonry","holy_grail","sticky_header","editorial"}

# Mapping from free-form to constrained
ELEMENT_MAP = {
    "navigation bar": "Navigation Bar", "nav bar": "Navigation Bar", "navbar": "Navigation Bar",
    "logo": "Navigation Bar", "menu button": "Navigation Bar", "nav links": "Navigation Bar",
    "bottom navigation bar": "Navigation Bar", "hamburger menu": "Navigation Bar",
    "sidebar": "Sidebar", "side menu": "Sidebar",
    "card": "Card", "feature card": "Card", "product card": "Card", "info card": "Card",
    "chart": "Chart", "graph": "Chart", "data visualization": "Chart",
    "button": "Button", "cta": "Button", "cta button": "Button", "cta link": "Button",
    "contact us button": "Button", "view toggle controls": "Button",
    "data table": "Data Table", "table": "Data Table",
    "form": "Form", "input": "Form", "form field": "Form", "text field": "Form",
    "avatar": "Avatar", "profile photo": "Avatar", "user icon": "Avatar",
    "badge": "Badge", "notification badge": "Badge", "label": "Badge",
    "tabs": "Tabs", "tab": "Tabs",
    "modal": "Modal", "dialog": "Modal", "popup": "Modal",
    "search bar": "Search Bar", "search": "Search Bar", "search input": "Search Bar",
    "toggle": "Toggle", "switch": "Toggle",
    "stats": "Stats", "stat counter": "Stats", "metric": "Stats",
    "hero section": "Hero Section", "hero": "Hero Section", "hero text": "Hero Section",
    "hero typography": "Hero Section", "hero tagline": "Hero Section",
    "dropdown": "Dropdown", "select": "Dropdown",
    "footer": "Footer", "footer bar": "Footer",
    "pricing table": "Pricing Table", "pricing": "Pricing Table",
    "image gallery": "Image Gallery", "gallery": "Image Gallery", "photo grid": "Image Gallery",
    "3d product grid": "Image Gallery", "3d product render": "Image Gallery",
    "full-bleed photography": "Image Gallery",
    "testimonials": "Testimonials", "reviews": "Testimonials",
    "icon grid": "Icon Grid", "feature grid": "Icon Grid",
    "timeline": "Timeline", "activity feed": "Timeline",
    "progress bar": "Progress Bar", "loading": "Progress Bar",
    "tag chips": "Tag Chips", "tags": "Tag Chips",
    "stepper": "Stepper", "wizard": "Stepper",
    "calendar": "Calendar",
    "file upload": "File Upload",
    "video player": "Video Player", "video": "Video Player",
    "tooltip": "Tooltip",
    "toast": "Toast", "notification": "Toast",
    "accordion": "Accordion",
    "breadcrumb": "Breadcrumb",
    "pagination": "Pagination", "dot navigation": "Pagination",
}

STYLE_MAP = {
    "minimal": "Minimal", "minimalist": "Minimal", "clean": "Minimal", "modern minimal": "Minimal",
    "bold": "Bold", "bold typography": "Bold", "maximalist": "Bold", "large typography": "Bold",
    "glassmorphism": "Glassmorphism", "frosted glass": "Glassmorphism",
    "gradient": "Gradient", "gradient background": "Gradient",
    "corporate": "Corporate", "business": "Corporate", "professional": "Corporate",
    "playful": "Playful", "fun": "Playful",
    "premium": "Premium", "luxury": "Premium", "elegant": "Premium",
    "futuristic": "Futuristic", "sci-fi": "Futuristic", "cinematic lighting": "Futuristic",
    "flat": "Flat",
    "3d": "3D", "3d rendering": "3D", "3d product rendering": "3D", "3d stickers": "3D",
    "isometric perspective": "3D",
    "dark": "Dark", "high contrast": "Dark",
    "editorial": "Editorial", "magazine-style": "Editorial", "fashion photography": "Editorial",
    "organic": "Organic", "natural": "Organic",
    "retro": "Retro", "vintage": "Retro",
    "geometric": "Geometric", "mirrored/symmetrical composition": "Geometric",
}

PAGE_MAP = {
    "landing": "Landing Page", "landing page": "Landing Page", "product-landing": "Landing Page",
    "hero-fullscreen": "Landing Page", "agency-landing": "Agency",
    "dashboard": "Dashboard", "admin": "Admin Panel",
    "e-commerce": "E-commerce", "product-showcase": "E-commerce", "shop": "E-commerce",
    "portfolio": "Portfolio", "editorial-feature": "Portfolio",
    "agency": "Agency", "studio": "Agency",
    "corporate": "Corporate", "business": "Corporate",
    "saas": "SaaS", "software": "SaaS",
    "blog": "Blog", "article": "Blog",
    "auth": "Auth", "login": "Auth", "signup": "Auth",
}

LAYOUT_MAP = {
    "hero-fullscreen": "full_bleed", "full-bleed-hero": "full_bleed", "full_bleed": "full_bleed",
    "centered-single-element": "single_column", "single_column": "single_column",
    "sidebar_detail": "sidebar_detail", "split_screen": "split_screen",
    "card_grid": "card_grid", "dashboard_panels": "dashboard_panels",
    "masonry": "masonry", "holy_grail": "holy_grail",
    "sticky_header": "sticky_header", "editorial": "editorial",
}


def normalize(results):
    """Normalize a list of vision results to constrained schema."""
    normalized = []
    for r in results:
        n = {}
        
        # Elements
        raw_elements = r.get("ui_elements", [])
        if isinstance(raw_elements, str):
            raw_elements = [raw_elements]
        elements = set()
        for el in raw_elements:
            el_lower = el.lower().strip()
            if el in VALID_ELEMENTS:
                elements.add(el)
            elif el_lower in ELEMENT_MAP:
                elements.add(ELEMENT_MAP[el_lower])
            else:
                # Try partial match
                for key, val in ELEMENT_MAP.items():
                    if key in el_lower or el_lower in key:
                        elements.add(val)
                        break
        n["ui_elements"] = sorted(elements)
        
        # Styles
        raw_styles = r.get("visual_style", [])
        if isinstance(raw_styles, str):
            raw_styles = [raw_styles]
        styles = set()
        for s in raw_styles:
            s_lower = s.lower().strip()
            if s in VALID_STYLES:
                styles.add(s)
            elif s_lower in STYLE_MAP:
                styles.add(STYLE_MAP[s_lower])
            else:
                for key, val in STYLE_MAP.items():
                    if key in s_lower or s_lower in key:
                        styles.add(val)
                        break
        n["visual_style"] = sorted(styles)
        
        # Page type
        raw_page = r.get("page_type", "")
        if raw_page in VALID_PAGES:
            n["page_type"] = raw_page
        elif raw_page.lower() in PAGE_MAP:
            n["page_type"] = PAGE_MAP[raw_page.lower()]
        else:
            n["page_type"] = "Landing Page"  # default
        
        # Layout
        raw_layout = r.get("layout_type", "")
        if raw_layout in VALID_LAYOUTS:
            n["layout_type"] = raw_layout
        elif raw_layout.lower() in LAYOUT_MAP:
            n["layout_type"] = LAYOUT_MAP[raw_layout.lower()]
        else:
            n["layout_type"] = "full_bleed"
        
        n["color_mode"] = r.get("color_mode", "light")
        n["quality_score"] = r.get("quality_score", 7)
        
        normalized.append(n)
    
    return normalized


if __name__ == "__main__":
    # Test with sample
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        result = normalize(data)
        print(json.dumps(result, indent=2))
