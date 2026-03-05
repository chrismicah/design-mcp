"""Ingest Awwwards site data into the design pattern database."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schema import DesignPattern, Platform
from database import DesignDatabase

AWWWARDS_SITES = [
    {
        "name": "The Renaissance Edition (Shopify)",
        "url": "https://www.shopify.com/editions/winter2026",
        "awwwards_url": "https://www.awwwards.com/sites/the-renaissance-edition",
        "tags": ["E-Commerce", "Technology", "Animation", "3D", "WebGL", "Shopify"],
        "scores": [7.92, 8.03, 7.51, 8.24],
        "page_type": "Landing Page",
        "visual_style": ["Futuristic", "Minimal"],
        "color_mode": "dark",
        "industry": "E-Commerce"
    },
    {
        "name": "The Future Label",
        "url": "https://www.awwwards.com/sites/the-future-label",
        "awwwards_url": "https://www.awwwards.com/sites/the-future-label",
        "tags": ["Design Agency", "Animation", "Creative"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Minimal", "Editorial"],
        "color_mode": "light",
        "industry": None
    },
    {
        "name": "The Kraken",
        "url": "https://www.awwwards.com/sites/the-kraken",
        "awwwards_url": "https://www.awwwards.com/sites/the-kraken",
        "tags": ["Animation", "Interactive", "WebGL"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Futuristic"],
        "color_mode": "dark",
        "industry": "Entertainment"
    },
    {
        "name": "Max Mara - Catch The Lantern",
        "url": "https://www.awwwards.com/sites/max-mara-catch-the-lantern",
        "awwwards_url": "https://www.awwwards.com/sites/max-mara-catch-the-lantern",
        "tags": ["Fashion", "Animation", "Interactive", "3D"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Luxury", "Minimal"],
        "color_mode": "dark",
        "industry": None
    },
    {
        "name": "Valentine's Day - Interactive Experience",
        "url": "https://www.awwwards.com/sites/valentines-day",
        "awwwards_url": "https://www.awwwards.com/sites/valentines-day",
        "tags": ["Animation", "Interactive", "Illustration"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Playful", "Organic"],
        "color_mode": "light",
        "industry": None
    },
    {
        "name": "The Way to Dream",
        "url": "https://www.awwwards.com/sites/the-way-to-dream",
        "awwwards_url": "https://www.awwwards.com/sites/the-way-to-dream",
        "tags": ["Scrolling", "Animation", "Parallax"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Organic", "Editorial"],
        "color_mode": "light",
        "industry": None
    },
    {
        "name": "The Branding People",
        "url": "https://www.awwwards.com/sites/the-branding-people",
        "awwwards_url": "https://www.awwwards.com/sites/the-branding-people",
        "tags": ["Design Agency", "Portfolio", "Minimal"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Minimal", "Corporate"],
        "color_mode": "light",
        "industry": None
    },
    {
        "name": "The Soul of the 911 (Porsche)",
        "url": "https://www.awwwards.com/sites/the-soul-of-the-911",
        "awwwards_url": "https://www.awwwards.com/sites/the-soul-of-the-911",
        "tags": ["Automotive", "Animation", "3D", "WebGL"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Luxury", "Futuristic"],
        "color_mode": "dark",
        "industry": None
    },
    {
        "name": "The Sculpt Society",
        "url": "https://www.awwwards.com/sites/the-sculpt-society",
        "awwwards_url": "https://www.awwwards.com/sites/the-sculpt-society",
        "tags": ["Fitness", "E-commerce", "Health"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Minimal", "Organic"],
        "color_mode": "light",
        "industry": "Health & Wellness"
    },
    {
        "name": "Institute of Health",
        "url": "https://www.awwwards.com/sites/institute-of-health",
        "awwwards_url": "https://www.awwwards.com/sites/institute-of-health",
        "tags": ["Health", "Corporate", "Clean"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Minimal", "Corporate"],
        "color_mode": "light",
        "industry": "Health & Wellness"
    },
    {
        "name": "Aramco - Shoot For The Future",
        "url": "https://www.awwwards.com/sites/aramco-shoot-for-the-future",
        "awwwards_url": "https://www.awwwards.com/sites/aramco-shoot-for-the-future",
        "tags": ["Corporate", "Animation", "Interactive", "WebGL"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Futuristic", "Corporate"],
        "color_mode": "dark",
        "industry": None
    },
    {
        "name": "The State of AI at Work (Asana)",
        "url": "https://www.awwwards.com/sites/the-state-of-ai-at-work",
        "awwwards_url": "https://www.awwwards.com/sites/the-state-of-ai-at-work",
        "tags": ["SaaS", "Data Visualization", "Interactive"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Minimal", "Corporate"],
        "color_mode": "light",
        "industry": "SaaS"
    },
    {
        "name": "Mouthful of Dust (State Library Victoria)",
        "url": "https://www.awwwards.com/sites/mouthful-of-dust",
        "awwwards_url": "https://www.awwwards.com/sites/mouthful-of-dust",
        "tags": ["Culture", "Interactive", "Storytelling", "Animation"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Editorial", "Organic"],
        "color_mode": "light",
        "industry": "Entertainment"
    },
    {
        "name": "The Real Estate Fund (DD.NYC)",
        "url": "https://www.awwwards.com/sites/the-real-estate-fund-dd-nyc-r",
        "awwwards_url": "https://www.awwwards.com/sites/the-real-estate-fund-dd-nyc-r",
        "tags": ["Real Estate", "Corporate", "Clean"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Luxury", "Corporate"],
        "color_mode": "light",
        "industry": "Real Estate"
    },
    {
        "name": "THE GRID",
        "url": "https://www.awwwards.com/sites/the-grid",
        "awwwards_url": "https://www.awwwards.com/sites/the-grid",
        "tags": ["Design Agency", "Animation", "Grid Layout"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Brutalist", "Futuristic"],
        "color_mode": "dark",
        "industry": None
    },
    {
        "name": "The Pendragon Cycle",
        "url": "https://www.awwwards.com/sites/the-pendragon-cycle",
        "awwwards_url": "https://www.awwwards.com/sites/the-pendragon-cycle",
        "tags": ["Storytelling", "Animation", "WebGL", "Interactive"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Futuristic", "Editorial"],
        "color_mode": "dark",
        "industry": "Entertainment"
    },
    {
        "name": "Miu Miu - The Holiday Diary",
        "url": "https://www.awwwards.com/sites/miu-miu-the-holiday-diary",
        "awwwards_url": "https://www.awwwards.com/sites/miu-miu-the-holiday-diary",
        "tags": ["Fashion", "Luxury", "Animation", "Interactive"],
        "scores": [],
        "page_type": "Landing Page",
        "visual_style": ["Luxury", "Editorial"],
        "color_mode": "light",
        "industry": None
    },
]


def main():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "patterns.json")
    db = DesignDatabase(db_path)
    existing_ids = {p.id for p in db._patterns}
    new_patterns = []

    for site in AWWWARDS_SITES:
        slug = site["awwwards_url"].split("/sites/")[-1]
        pattern_id = f"awwwards-{slug}"

        if pattern_id in existing_ids:
            continue

        avg_score = sum(site["scores"]) / len(site["scores"]) if site["scores"] else None
        quality = round(avg_score, 1) if avg_score else 8.0  # Awwwards sites are generally high quality

        pattern = DesignPattern(
            id=pattern_id,
            name=site["name"],
            source="awwwards",
            source_url=site["awwwards_url"],
            page_type=site["page_type"],
            ux_patterns=[],
            ui_elements=[],
            industry=site.get("industry"),
            layout_type=None,
            platform=Platform.WEB,
            color_mode=site.get("color_mode"),
            visual_style=site.get("visual_style", []),
            primary_colors=[],
            behavioral_description=None,
            component_hints=[],
            accessibility_notes=None,
            semantic_tokens=None,
            quality_score=quality,
            tags=["awwwards", "award-winning"] + [t.lower().replace(" ", "-") for t in site["tags"]]
        )
        new_patterns.append(pattern)
        existing_ids.add(pattern_id)

    if new_patterns:
        db.add_batch(new_patterns)
        print(f"Added {len(new_patterns)} Awwwards patterns (total: {db.count()})")
    else:
        print("No new Awwwards patterns to add")


if __name__ == "__main__":
    main()
