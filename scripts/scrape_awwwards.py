"""Scrape Awwwards Sites of the Day for high-quality design patterns + screenshots."""
import json
import re
import sys
import time
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from schema import DesignPattern, Platform, LayoutType

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots" / "awwwards"
DATA_PATH = Path(__file__).parent.parent / "data" / "patterns.json"

SITES = [
    "adovasio", "gavin-schneider-productions", "jason-bergh", "shift-5",
    "ava-srg", "neon-rated", "cathy-dolle-portfolio-1", "1820-productions",
    "studio-dado", "dulcedo", "oceanx-2025", "d2c-life-science",
    "voku-studiotm", "vibrant-wellness", "farm-minerals", "studio-dialect",
    "mob-links", "telha-clarke", "lightweight", "damn-good-brands-2",
    "valiente", "art-here-2025-richard-mille", "emilie-aubry", "sileent",
    "the-renaissance-edition", "nicola-romeitm", "nfinite", "ciridae",
    "aramco-shoot-for-the-future", "explore-primland", "c-design-by-dylan"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9"
}


def scrape_site(client: httpx.Client, slug: str) -> dict | None:
    """Scrape a single Awwwards site detail page."""
    url = f"https://www.awwwards.com/sites/{slug}"
    try:
        resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        if resp.status_code != 200:
            print(f"  [{resp.status_code}] {slug}", flush=True)
            return None
        html = resp.text
    except Exception as e:
        print(f"  [ERROR] {slug}: {e}", flush=True)
        return None

    # Extract title
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()
    title = re.sub(r'<[^>]+>', '', title).strip()

    # Extract screenshot URL (og:image or main screenshot)
    og_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
    screenshot_url = og_match.group(1) if og_match else None

    # Extract site URL
    site_url_match = re.search(r'class="[^"]*visit[^"]*"[^>]*href="([^"]+)"', html, re.IGNORECASE)
    if not site_url_match:
        site_url_match = re.search(r'Visit\s+Site.*?href="([^"]+)"', html, re.DOTALL)
    site_url = site_url_match.group(1) if site_url_match else url

    # Extract tags/categories
    tag_matches = re.findall(r'/websites/([a-z0-9-]+)/"', html)
    tags = list(set(tag_matches))[:10]

    # Extract studio/agency
    studio_match = re.search(r'class="[^"]*designer[^"]*"[^>]*>.*?<strong>([^<]+)</strong>', html, re.DOTALL)
    studio = studio_match.group(1).strip() if studio_match else None

    # Try to get scores
    scores = re.findall(r'(\d+\.\d+)\s*(?:/\s*10)?', html[:5000])

    return {
        "slug": slug,
        "title": title,
        "awwwards_url": url,
        "site_url": site_url,
        "screenshot_url": screenshot_url,
        "tags": tags,
        "studio": studio,
    }


def download_screenshot(client: httpx.Client, url: str, slug: str) -> str | None:
    """Download a screenshot and return local path."""
    if not url:
        return None
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ext = "jpg"
    if ".png" in url:
        ext = "png"
    elif ".webp" in url:
        ext = "webp"
    filepath = SCREENSHOTS_DIR / f"{slug}.{ext}"
    if filepath.exists():
        return str(filepath.relative_to(Path(__file__).parent.parent))
    try:
        resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 1000:
            filepath.write_bytes(resp.content)
            return str(filepath.relative_to(Path(__file__).parent.parent))
    except Exception as e:
        print(f"  [DL ERROR] {slug}: {e}", flush=True)
    return None


def main():
    print(f"Scraping {len(SITES)} Awwwards SOTD sites...", flush=True)

    with open(DATA_PATH) as f:
        existing = json.load(f)
    existing_ids = {p["id"] for p in existing}

    new_patterns = []
    client = httpx.Client()

    for i, slug in enumerate(SITES):
        pattern_id = f"awwwards-{slug}"
        if pattern_id in existing_ids:
            print(f"  [{i+1}/{len(SITES)}] SKIP {slug} (exists)", flush=True)
            continue

        print(f"  [{i+1}/{len(SITES)}] {slug}...", flush=True)
        data = scrape_site(client, slug)
        if not data:
            continue

        # Download screenshot
        local_img = download_screenshot(client, data["screenshot_url"], slug)

        pattern = DesignPattern(
            id=pattern_id,
            name=data["title"],
            source="awwwards",
            source_url=data["awwwards_url"],
            image_url=data["screenshot_url"],
            page_type="Landing Page",
            ux_patterns=[],
            ui_elements=[],
            industry=None,
            layout_type=None,
            platform=Platform.WEB,
            color_mode=None,
            visual_style=["Editorial"],
            primary_colors=[],
            behavioral_description=None,
            component_hints=[],
            accessibility_notes=None,
            semantic_tokens=None,
            quality_score=7.5,  # Awwwards SOTD = high quality baseline
            tags=["awwwards", "sotd", "award-winning"] + data["tags"][:5]
        )
        new_patterns.append(pattern.model_dump())
        existing_ids.add(pattern_id)
        time.sleep(1.5)  # Rate limit

    client.close()

    if new_patterns:
        all_patterns = existing + new_patterns
        with open(DATA_PATH, "w") as f:
            json.dump(all_patterns, f, indent=2)
        print(f"\nAdded {len(new_patterns)} Awwwards patterns. Total: {len(all_patterns)}", flush=True)
    else:
        print("\nNo new patterns to add.", flush=True)

    # Report screenshot status
    ss_files = list(SCREENSHOTS_DIR.glob("*")) if SCREENSHOTS_DIR.exists() else []
    print(f"Screenshots downloaded: {len(ss_files)}", flush=True)


if __name__ == "__main__":
    main()
