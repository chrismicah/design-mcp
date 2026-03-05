"""
Parse Dribbble snapshot data and add to the design pattern database.
Takes structured data extracted from browser snapshots.
"""
import json
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase

TAXONOMY_TAGS_TO_PAGE_TYPE = {
    "dashboard": "Dashboard", "pricing": "Pricing", "landing": "Landing Page",
    "onboarding": "Onboarding", "login": "Login", "signup": "Signup",
    "settings": "Settings", "checkout": "Checkout", "404": "404 Page",
    "profile": "Profile", "admin": "Admin Panel", "analytics": "Analytics",
    "chat": "Chat Interface", "calendar": "Calendar", "kanban": "Kanban Board",
    "notification": "Notifications", "file": "File Explorer", "docs": "Documentation",
    "marketplace": "Marketplace", "social": "Social Feed", "invoice": "Invoice",
    "email": "Email Template",
}

TAXONOMY_TAGS_TO_INDUSTRY = {
    "crypto": "Fintech", "bitcoin": "Fintech", "fintech": "Fintech", "banking": "Fintech",
    "finance": "Fintech", "wallet": "Fintech", "trading": "Fintech",
    "ecommerce": "E-Commerce", "shop": "E-Commerce", "store": "E-Commerce",
    "saas": "SaaS", "b2b": "SaaS", "crm": "CRM",
    "health": "Health & Wellness", "fitness": "Health & Wellness", "medical": "Health & Wellness",
    "education": "Education", "learning": "Education",
    "social": "Social Media", "chat": "Social Media", "messaging": "Social Media",
    "productivity": "Productivity", "task": "Productivity", "project": "Productivity",
    "travel": "Travel", "booking": "Travel",
    "food": "Food & Delivery", "delivery": "Food & Delivery", "restaurant": "Food & Delivery",
}

TAXONOMY_TAGS_TO_STYLE = {
    "minimal": "Minimal", "minimalist": "Minimal", "clean": "Minimal",
    "glassmorphism": "Glassmorphism", "gradient": "Gradient-Heavy",
    "brutalist": "Brutalist", "flat": "Flat", "material": "Material",
    "skeuomorphic": "Skeuomorphic", "skeuomorph": "Skeuomorphic", "skeumorphism": "Skeuomorphic",
    "retro": "Retro", "futuristic": "Futuristic", "modern": "Minimal",
    "corporate": "Corporate", "playful": "Playful",
}

UI_ELEMENT_TAGS = {
    "sidebar": "Sidebar", "navigation": "Navigation Bar", "card": "Card",
    "table": "Data Table", "chart": "Data Table", "graph": "Data Table",
    "modal": "Modal", "dropdown": "Dropdown", "button": "Button",
    "input": "Input", "avatar": "Avatar", "badge": "Badge",
    "tabs": "Tabs", "carousel": "Carousel", "slider": "Slider",
    "toggle": "Toggle", "tooltip": "Tooltip", "pagination": "Pagination",
}


def parse_dribbble_shot(title: str, tags_str: str, url: str, designer: str, likes: str, views: str, search_query: str) -> DesignPattern:
    """Parse a single Dribbble shot into a DesignPattern."""
    tags_lower = tags_str.lower()
    title_lower = title.lower()
    combined = f"{title_lower} {tags_lower}"

    # Infer page type
    page_type = "Landing Page"  # default
    for keyword, pt in TAXONOMY_TAGS_TO_PAGE_TYPE.items():
        if keyword in combined:
            page_type = pt
            break

    # Infer industry
    industry = None
    for keyword, ind in TAXONOMY_TAGS_TO_INDUSTRY.items():
        if keyword in combined:
            industry = ind
            break

    # Infer visual styles
    visual_styles = []
    for keyword, style in TAXONOMY_TAGS_TO_STYLE.items():
        if keyword in combined and style not in visual_styles:
            visual_styles.append(style)

    # Infer color mode
    color_mode = None
    if "dark" in combined:
        color_mode = "dark"
    elif "light" in combined:
        color_mode = "light"

    # Infer UI elements
    ui_elements = []
    for keyword, element in UI_ELEMENT_TAGS.items():
        if keyword in combined and element not in ui_elements:
            ui_elements.append(element)

    # Extract tags
    tag_list = [t.strip() for t in tags_str.split() if len(t.strip()) > 2]

    # Parse likes/views for quality score
    quality = 5.0
    try:
        view_num = float(views.replace("k", "000").replace(".", ""))
        like_num = float(likes.replace(",", ""))
        if view_num > 50000:
            quality = 9.0
        elif view_num > 20000:
            quality = 8.0
        elif view_num > 10000:
            quality = 7.0
        elif view_num > 5000:
            quality = 6.0
    except:
        pass

    # Generate ID from URL
    shot_id = url.split("/")[-1][:50] if url else title.replace(" ", "-")[:50]

    return DesignPattern(
        id=f"dribbble-{shot_id}",
        name=title,
        source="dribbble",
        source_url=f"https://dribbble.com{url}" if url.startswith("/") else url,
        page_type=page_type,
        ux_patterns=[],
        ui_elements=ui_elements,
        industry=industry,
        layout_type=None,
        platform=Platform.WEB,
        color_mode=color_mode,
        visual_style=visual_styles,
        primary_colors=[],
        behavioral_description=None,
        component_hints=[],
        accessibility_notes=None,
        semantic_tokens=None,
        quality_score=quality,
        tags=tag_list[:20] + ["dribbble", search_query.replace(" ", "-")]
    )


def ingest_shots(shots_data: list[dict], search_query: str):
    """Ingest a list of shot data dicts into the database."""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "patterns.json")
    db = DesignDatabase(db_path)

    existing_ids = {p.id for p in db._patterns}
    new_patterns = []

    for shot in shots_data:
        pattern = parse_dribbble_shot(
            title=shot["title"],
            tags_str=shot.get("tags", ""),
            url=shot.get("url", ""),
            designer=shot.get("designer", ""),
            likes=shot.get("likes", "0"),
            views=shot.get("views", "0"),
            search_query=search_query
        )
        if pattern.id not in existing_ids:
            new_patterns.append(pattern)
            existing_ids.add(pattern.id)

    if new_patterns:
        db.add_batch(new_patterns)
        print(f"Added {len(new_patterns)} new patterns from '{search_query}' (total: {db.count()})")
    else:
        print(f"No new patterns from '{search_query}' (all duplicates)")

    return len(new_patterns)


if __name__ == "__main__":
    # Test with sample data
    test_shots = [
        {
            "title": "Test Dashboard Dark Mode",
            "tags": "dashboard dark mode saas minimal sidebar",
            "url": "/shots/12345-test",
            "designer": "Test Designer",
            "likes": "50",
            "views": "10k"
        }
    ]
    ingest_shots(test_shots, "test")
