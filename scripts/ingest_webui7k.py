"""
Ingest biglab/webui-7kbal dataset into the DesignPattern database.
Processes 6,402 samples: reads HTML, accessibility trees, CSS classes, URLs.
Skips screenshots — structured metadata > images for LLM UI generation.
"""

import json
import gzip
import os
import sys
import re
from pathlib import Path
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase

DATASET_DIR = Path(__file__).parent.parent / "data" / "webui-7kbal" / "balanced_7k"


def read_gz_json(path: Path) -> dict | list | None:
    """Read a gzipped JSON file."""
    try:
        with gzip.open(path, 'rt', encoding='utf-8', errors='ignore') as f:
            return json.load(f)
    except Exception:
        return None


def read_text(path: Path) -> str:
    """Read a text file."""
    try:
        return path.read_text(encoding='utf-8', errors='ignore').strip()
    except Exception:
        return ""


def infer_page_type(url: str, html: str, axtree: dict | list | None) -> str:
    """Infer page type from URL, HTML content, and accessibility tree."""
    url_lower = url.lower()
    html_lower = html.lower()[:5000]  # Only check first 5KB

    # URL-based heuristics (most reliable)
    url_rules = [
        (["/pricing", "/plans", "/packages"], "Pricing"),
        (["/login", "/signin", "/sign-in"], "Login"),
        (["/signup", "/register", "/sign-up", "/join"], "Signup"),
        (["/dashboard", "/admin/dashboard", "/app/dashboard"], "Dashboard"),
        (["/settings", "/preferences", "/account"], "Settings"),
        (["/blog", "/post/", "/article"], "Blog Post"),
        (["/cart", "/checkout", "/payment"], "Checkout"),
        (["/404", "/not-found"], "404 Page"),
        (["/docs", "/documentation", "/api-reference", "/guide"], "Documentation"),
        (["/profile", "/user/", "/@"], "Profile"),
        (["/search", "/results"], "Search Results"),
        (["/onboarding", "/welcome", "/get-started"], "Onboarding"),
        (["/analytics", "/metrics", "/reports"], "Analytics"),
        (["/calendar", "/schedule"], "Calendar"),
        (["/chat", "/messages", "/inbox"], "Chat Interface"),
        (["/notifications"], "Notifications"),
        (["/marketplace", "/store", "/shop"], "Marketplace"),
        (["/product/", "/item/"], "Product Page"),
        (["/feed", "/timeline"], "Social Feed"),
        (["/kanban", "/board"], "Kanban Board"),
        (["/files", "/documents", "/drive"], "File Explorer"),
    ]

    for patterns, page_type in url_rules:
        if any(p in url_lower for p in patterns):
            return page_type

    # HTML content heuristics
    if "<nav" in html_lower and ("hero" in html_lower or "cta" in html_lower):
        return "Landing Page"
    if "price" in html_lower and ("month" in html_lower or "/yr" in html_lower or "annual" in html_lower):
        return "Pricing"
    if '<form' in html_lower and ('password' in html_lower or 'login' in html_lower):
        return "Login"
    if '<form' in html_lower and 'sign' in html_lower and 'up' in html_lower:
        return "Signup"
    if 'dashboard' in html_lower:
        return "Dashboard"
    if '<table' in html_lower and ('admin' in html_lower or 'manage' in html_lower):
        return "Admin Panel"

    return "Landing Page"  # Default


def infer_industry(url: str, html: str) -> str | None:
    """Infer industry from URL and HTML content."""
    combined = (url + " " + html[:3000]).lower()

    industry_signals = {
        "Fintech": ["finance", "bank", "crypto", "payment", "wallet", "trading", "invest"],
        "E-Commerce": ["shop", "store", "product", "cart", "ecommerce", "buy", "price"],
        "Health & Wellness": ["health", "medical", "fitness", "doctor", "patient", "wellness"],
        "Education": ["learn", "course", "student", "education", "teach", "academy"],
        "SaaS": ["saas", "subscription", "api", "platform", "integrate"],
        "Social Media": ["social", "post", "follow", "share", "feed", "friend"],
        "Productivity": ["task", "project", "calendar", "todo", "kanban", "productivity"],
        "Developer Tools": ["github", "code", "developer", "api", "deploy", "repository"],
        "Travel": ["travel", "hotel", "flight", "booking", "destination"],
        "Food & Delivery": ["food", "restaurant", "delivery", "menu", "order"],
        "Entertainment": ["video", "music", "stream", "movie", "game"],
        "Real Estate": ["property", "real estate", "house", "apartment", "rent"],
    }

    for industry, signals in industry_signals.items():
        matches = sum(1 for s in signals if s in combined)
        if matches >= 2:
            return industry

    return None


def infer_ui_elements(html: str, axtree: dict | list | None) -> list[str]:
    """Infer UI elements from HTML and accessibility tree."""
    elements = []
    html_lower = html.lower()[:10000]

    element_signals = {
        "Navigation Bar": ["<nav", "navbar", "navigation"],
        "Button": ["<button", 'role="button"', "btn"],
        "Card": ['class="card"', "card-body", "card-header", "card-"],
        "Modal": ["modal", 'role="dialog"'],
        "Input": ['<input', '<textarea'],
        "Dropdown": ["dropdown", '<select'],
        "Tabs": ['role="tab"', "tab-content", "tab-pane"],
        "Accordion": ["accordion", "collapse"],
        "Badge": ["badge"],
        "Avatar": ["avatar"],
        "Carousel": ["carousel", "slider", "swiper"],
        "Progress Bar": ["progress"],
        "Tooltip": ["tooltip"],
        "Breadcrumb": ["breadcrumb"],
        "Pagination": ["pagination"],
        "Toast": ["toast", "notification"],
        "Sidebar": ["sidebar", "side-bar", "sidenav"],
        "Data Table": ["<table", "data-table", "datatable"],
        "Toggle": ["toggle", "switch"],
        "Icon": ["icon", "svg", "fa-"],
        "Divider": ["divider", "<hr"],
        "Chip": ["chip", "tag"],
        "Code Snippet": ["<code", "<pre", "highlight"],
        "Date Picker": ["datepicker", "date-picker"],
        "File Upload": ["file-upload", "dropzone", 'type="file"'],
    }

    for element_name, signals in element_signals.items():
        if any(signal in html_lower for signal in signals):
            elements.append(element_name)

    return elements[:15]  # Cap at 15 to avoid noise


def infer_layout_type(html: str, box_data: dict | list | None) -> LayoutType | None:
    """Infer layout type from HTML classes and box model data."""
    html_lower = html.lower()[:10000]

    if "sidebar" in html_lower or "side-bar" in html_lower or "sidenav" in html_lower:
        return LayoutType.SIDEBAR_MAIN
    if "grid" in html_lower and ("col-" in html_lower or "grid-cols" in html_lower):
        return LayoutType.CSS_GRID
    if "masonry" in html_lower:
        return LayoutType.MASONRY
    if "flex" in html_lower:
        return LayoutType.FLEXBOX
    if "split" in html_lower:
        return LayoutType.SPLIT_SCREEN

    return None


def infer_color_mode(html: str, style_data: dict | list | None) -> str | None:
    """Infer light/dark mode from styles and HTML."""
    html_lower = html.lower()[:5000]

    if "dark-mode" in html_lower or "dark-theme" in html_lower or 'data-theme="dark"' in html_lower:
        return "dark"
    if "light-mode" in html_lower or "light-theme" in html_lower:
        return "light"

    # Check background color in styles
    if style_data and isinstance(style_data, dict):
        bg = str(style_data.get("background-color", "")).lower()
        if bg:
            # Dark backgrounds
            if any(dark in bg for dark in ["#000", "#111", "#121", "#1a1", "#222", "rgb(0", "rgb(17", "rgb(18", "rgb(26", "rgb(34"]):
                return "dark"

    return None


def infer_visual_style(html: str) -> list[str]:
    """Infer visual style from CSS classes and HTML content."""
    styles = []
    html_lower = html.lower()[:10000]

    if any(x in html_lower for x in ["tailwind", "tw-", "shadow-", "rounded-"]):
        styles.append("Minimal")
    if any(x in html_lower for x in ["bootstrap", "btn-primary", "container-fluid"]):
        styles.append("Corporate")
    if any(x in html_lower for x in ["material", "mdc-", "mat-"]):
        styles.append("Material")
    if any(x in html_lower for x in ["glassmorphism", "backdrop-blur", "glass"]):
        styles.append("Glassmorphism")
    if any(x in html_lower for x in ["gradient", "bg-gradient"]):
        styles.append("Gradient-Heavy")

    return styles[:3]


def extract_css_frameworks(html: str) -> list[str]:
    """Extract CSS frameworks used."""
    frameworks = []
    html_lower = html.lower()

    if "tailwind" in html_lower or "tw-" in html_lower:
        frameworks.append("tailwind")
    if "bootstrap" in html_lower:
        frameworks.append("bootstrap")
    if "material" in html_lower:
        frameworks.append("material")
    if "bulma" in html_lower:
        frameworks.append("bulma")
    if "chakra" in html_lower:
        frameworks.append("chakra")
    if "ant-" in html_lower or "antd" in html_lower:
        frameworks.append("antd")

    return frameworks


def process_sample(sample_dir: Path) -> DesignPattern | None:
    """Process a single webui-7kbal sample into a DesignPattern."""
    sample_id = sample_dir.name

    # Use desktop resolution (1280x720) as primary
    prefix = "default_1280-720"

    # Read files
    html_path = sample_dir / f"{prefix}-html.html"
    axtree_path = sample_dir / f"{prefix}-axtree.json.gz"
    bb_path = sample_dir / f"{prefix}-bb.json.gz"
    box_path = sample_dir / f"{prefix}-box.json.gz"
    class_path = sample_dir / f"{prefix}-class.json.gz"
    style_path = sample_dir / f"{prefix}-style.json.gz"
    url_path = sample_dir / f"{prefix}-url.txt"
    links_path = sample_dir / f"{prefix}-links.json"

    html = read_text(html_path)
    if not html or len(html) < 50:
        return None  # Skip broken entries

    url = read_text(url_path)
    axtree = read_gz_json(axtree_path)
    box_data = read_gz_json(box_path)
    style_data = read_gz_json(style_path)
    class_data = read_gz_json(class_path)

    # Extract metadata
    page_type = infer_page_type(url, html, axtree)
    industry = infer_industry(url, html)
    ui_elements = infer_ui_elements(html, axtree)
    layout_type = infer_layout_type(html, box_data)
    color_mode = infer_color_mode(html, style_data)
    visual_style = infer_visual_style(html)
    frameworks = extract_css_frameworks(html)

    # Extract title from HTML
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip()[:100] if title_match else f"WebUI {sample_id}"

    # Build tags
    tags = ["webui-7kbal"]
    tags.extend(frameworks)
    if color_mode:
        tags.append(f"{color_mode}-mode")
    if industry:
        tags.append(industry.lower().replace(" & ", "-").replace(" ", "-"))

    return DesignPattern(
        id=f"webui7k-{sample_id}",
        name=title if title and title != "WebUI" else f"WebUI Sample {sample_id}",
        source="webui-7kbal",
        source_url=url or f"https://huggingface.co/datasets/biglab/webui-7kbal",
        page_type=page_type,
        ux_patterns=[],
        ui_elements=ui_elements,
        industry=industry,
        layout_type=layout_type,
        platform=Platform.WEB,
        color_mode=color_mode,
        visual_style=visual_style,
        primary_colors=[],
        behavioral_description=None,
        component_hints=[],
        accessibility_notes=None,
        semantic_tokens=None,
        quality_score=None,
        tags=tags
    )


def main():
    db_path = str(Path(__file__).parent.parent / "data" / "patterns.json")
    db = DesignDatabase(db_path)

    existing_count = db.count()
    print(f"Existing patterns: {existing_count}")

    if not DATASET_DIR.exists():
        print(f"Dataset directory not found: {DATASET_DIR}")
        return

    sample_dirs = sorted([d for d in DATASET_DIR.iterdir() if d.is_dir()])
    total = len(sample_dirs)
    print(f"Found {total} sample directories")

    # Process in batches for memory efficiency
    BATCH_SIZE = 500
    new_count = 0
    skipped = 0
    page_type_counts = Counter()

    existing_ids = {p.id for p in db._patterns}
    batch = []

    for i, sample_dir in enumerate(sample_dirs):
        pattern = process_sample(sample_dir)

        if pattern is None:
            skipped += 1
            continue

        if pattern.id in existing_ids:
            skipped += 1
            continue

        batch.append(pattern)
        existing_ids.add(pattern.id)
        page_type_counts[pattern.page_type] += 1
        new_count += 1

        if len(batch) >= BATCH_SIZE:
            db.add_batch(batch)
            batch = []
            print(f"  Progress: {i+1}/{total} processed, {new_count} added, {skipped} skipped")

    # Final batch
    if batch:
        db.add_batch(batch)

    print(f"\n{'='*50}")
    print(f"Ingestion complete!")
    print(f"  Processed: {total}")
    print(f"  New patterns added: {new_count}")
    print(f"  Skipped (broken/duplicate): {skipped}")
    print(f"  Total in database: {db.count()}")
    print(f"\nPage type distribution:")
    for pt, count in page_type_counts.most_common():
        print(f"  {pt}: {count}")


if __name__ == "__main__":
    main()
