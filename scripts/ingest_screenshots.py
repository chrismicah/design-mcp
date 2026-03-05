"""
Ingest all screenshot-based patterns into the database.
Creates DesignPattern entries for Dribbble, Awwwards, Curated, and Landbook screenshots
that don't already have corresponding patterns.
"""
import json
import os
import sys
import re
import hashlib
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase

BASE_DIR = Path(__file__).parent.parent
DB_PATH = str(BASE_DIR / "data" / "patterns.json")

# Mapping of screenshot filenames to design metadata
# These are inferred from Dribbble tags, Awwwards categories, and filename hints

def infer_from_filename(filename: str, source: str) -> dict:
    """Infer design metadata from screenshot filename."""
    name_lower = filename.lower()
    
    # Page type inference
    page_type = "Landing Page"  # default
    page_rules = [
        (["dashboard", "admin", "analytics", "metrics"], "Dashboard"),
        (["pricing", "plans", "subscription"], "Pricing"),
        (["login", "signin", "sign-in"], "Login"),
        (["signup", "register", "sign-up"], "Signup"),
        (["settings", "preferences", "account"], "Settings"),
        (["profile", "user-profile"], "Profile"),
        (["checkout", "cart", "payment"], "Checkout"),
        (["blog", "article", "post"], "Blog Post"),
        (["docs", "documentation"], "Documentation"),
        (["onboarding", "welcome", "get-started"], "Onboarding"),
        (["chat", "messenger", "inbox"], "Chat Interface"),
        (["calendar", "schedule"], "Calendar"),
        (["kanban", "board", "task"], "Kanban Board"),
        (["ecommerce", "shop", "store", "product"], "Product Page"),
        (["portfolio", "folio", "showcase"], "Landing Page"),
        (["crypto", "defi", "wallet", "token"], "Dashboard"),
        (["saas", "platform"], "Landing Page"),
        (["mobile", "app"], "Landing Page"),
    ]
    for keywords, ptype in page_rules:
        if any(k in name_lower for k in keywords):
            page_type = ptype
            break
    
    # Industry inference
    industry = None
    industry_rules = [
        (["crypto", "defi", "blockchain", "token", "wallet", "fintech", "finance", "bank", "payment"], "Fintech"),
        (["ecommerce", "shop", "store", "product", "cart"], "E-Commerce"),
        (["health", "medical", "fitness", "wellness"], "Health & Wellness"),
        (["education", "learn", "course", "school"], "Education"),
        (["saas", "platform", "api"], "SaaS"),
        (["social", "community", "feed"], "Social Media"),
        (["ai", "machine-learning", "chatbot"], "Developer Tools"),
        (["travel", "hotel", "booking"], "Travel"),
        (["food", "restaurant", "delivery"], "Food & Delivery"),
        (["real-estate", "property", "house"], "Real Estate"),
    ]
    for keywords, ind in industry_rules:
        if any(k in name_lower for k in keywords):
            industry = ind
            break
    
    # Color mode inference
    color_mode = None
    if "dark" in name_lower:
        color_mode = "dark"
    elif "light" in name_lower:
        color_mode = "light"
    
    # Visual style
    visual_style = []
    if any(x in name_lower for x in ["minimal", "clean", "simple"]):
        visual_style.append("Minimal")
    if any(x in name_lower for x in ["gradient", "colorful"]):
        visual_style.append("Gradient-Heavy")
    if "glass" in name_lower:
        visual_style.append("Glassmorphism")
    if any(x in name_lower for x in ["modern", "sleek"]):
        visual_style.append("Minimal")
    
    # UI elements from filename
    ui_elements = []
    element_rules = [
        (["card"], "Card"),
        (["table", "data"], "Data Table"),
        (["chart", "graph", "analytics"], "Progress Bar"),
        (["modal", "dialog"], "Modal"),
        (["sidebar", "nav"], "Sidebar"),
        (["form", "input"], "Input"),
        (["button", "cta"], "Button"),
    ]
    for keywords, elem in element_rules:
        if any(k in name_lower for k in keywords):
            ui_elements.append(elem)
    
    # Tags
    tags = [source]
    if color_mode:
        tags.append(f"{color_mode}-mode")
    # Extract meaningful words from filename
    words = re.findall(r'[a-z]+', name_lower)
    skip_words = {'the', 'and', 'for', 'web', 'design', 'page', 'png', 'jpg', 'webp', 'jpeg', 'still', 'file', 'dribbble'}
    tags.extend([w for w in words if len(w) > 3 and w not in skip_words][:5])
    
    # Clean name
    name = filename.rsplit('.', 1)[0]
    name = re.sub(r'^(dribbble-|awwwards-)', '', name)
    name = name.replace('-', ' ').replace('_', ' ').title()
    if len(name) < 5:
        name = f"{source.title()} Design {hashlib.md5(filename.encode()).hexdigest()[:6]}"
    
    return {
        "name": name,
        "page_type": page_type,
        "industry": industry,
        "color_mode": color_mode,
        "visual_style": visual_style,
        "ui_elements": ui_elements,
        "tags": tags,
    }


def main():
    db = DesignDatabase(DB_PATH)
    existing_ids = {p.id for p in db._patterns}
    print(f"Existing patterns: {len(existing_ids)}", flush=True)
    
    new_patterns = []
    sources_to_scan = {
        "dribbble": BASE_DIR / "screenshots" / "dribbble",
        "awwwards": BASE_DIR / "screenshots" / "awwwards",
        "curated": BASE_DIR / "screenshots" / "curated",
        "landbook": BASE_DIR / "screenshots" / "landbook",
    }
    
    for source, screenshot_dir in sources_to_scan.items():
        if not screenshot_dir.exists():
            continue
        
        files = sorted(screenshot_dir.glob("*"))
        added = 0
        for f in files:
            if f.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif'):
                continue
            if f.stat().st_size < 10000:  # Skip tiny files
                continue
            
            # Generate stable ID from filename
            pattern_id = f"screenshot-{source}-{hashlib.md5(f.name.encode()).hexdigest()[:10]}"
            if pattern_id in existing_ids:
                continue
            
            meta = infer_from_filename(f.name, source)
            
            pattern = DesignPattern(
                id=pattern_id,
                name=meta["name"],
                source=source,
                source_url=f"screenshots/{source}/{f.name}",
                image_url=f"screenshots/{source}/{f.name}",
                page_type=meta["page_type"],
                ux_patterns=[],
                ui_elements=meta["ui_elements"],
                industry=meta["industry"],
                layout_type=None,
                platform=Platform.WEB,
                color_mode=meta["color_mode"],
                visual_style=meta["visual_style"],
                primary_colors=[],
                behavioral_description=None,
                component_hints=[],
                accessibility_notes=None,
                semantic_tokens=None,
                quality_score=None,
                tags=meta["tags"],
            )
            new_patterns.append(pattern)
            existing_ids.add(pattern_id)
            added += 1
        
        print(f"  {source}: {added} new patterns from {len(files)} screenshots", flush=True)
    
    if new_patterns:
        db.add_batch(new_patterns)
        print(f"\nAdded {len(new_patterns)} new screenshot-based patterns", flush=True)
    
    print(f"Total patterns: {db.count()}", flush=True)


if __name__ == "__main__":
    main()
