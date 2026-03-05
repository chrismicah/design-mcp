"""
Bulk scraper: Gather 1000+ high-quality design screenshots from multiple sources.
Sources: Awwwards, Land-book, Lapa.ninja, curated SaaS sites.
"""
import json
import re
import sys
import time
import os
from pathlib import Path
from urllib.parse import quote, urljoin

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from schema import DesignPattern, Platform, LayoutType

BASE_DIR = Path(__file__).parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
DATA_PATH = BASE_DIR / "data" / "patterns.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}


def load_existing():
    with open(DATA_PATH) as f:
        return json.load(f)


def save_patterns(existing, new_patterns):
    all_p = existing + new_patterns
    with open(DATA_PATH, "w") as f:
        json.dump(all_p, f, indent=2)
    return len(all_p)


def download_image(client, url, filepath):
    """Download image, return True if successful and decent quality."""
    if filepath.exists() and filepath.stat().st_size > 5000:
        return True
    try:
        resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 5000:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False


def get_extension(url):
    if ".png" in url.lower():
        return "png"
    if ".webp" in url.lower():
        return "webp"
    return "jpg"


# =============================================================
# SOURCE 1: AWWWARDS (pages 2-10)
# =============================================================
def scrape_awwwards(client, existing_ids, max_count=270):
    """Scrape Awwwards SOTD pages 2-10."""
    print(f"\n{'='*60}", flush=True)
    print("SOURCE: AWWWARDS (Sites of the Day)", flush=True)
    print(f"{'='*60}", flush=True)

    ss_dir = SCREENSHOTS_DIR / "awwwards"
    ss_dir.mkdir(parents=True, exist_ok=True)
    new_patterns = []

    for page in range(2, 12):
        if len(new_patterns) >= max_count:
            break

        url = f"https://www.awwwards.com/websites/sites_of_the_day/?page={page}"
        print(f"  Page {page}...", flush=True)

        try:
            resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
            if resp.status_code != 200:
                print(f"    [{resp.status_code}] skipping", flush=True)
                continue
        except Exception as e:
            print(f"    [ERROR] {e}", flush=True)
            continue

        html = resp.text
        # Extract site links
        site_links = re.findall(r'href="/sites/([a-z0-9-]+)"', html)
        slugs = list(dict.fromkeys(site_links))  # dedupe preserving order
        print(f"    Found {len(slugs)} sites", flush=True)

        for slug in slugs:
            if len(new_patterns) >= max_count:
                break
            pid = f"awwwards-{slug}"
            if pid in existing_ids:
                continue

            # Get site detail page
            detail_url = f"https://www.awwwards.com/sites/{slug}"
            try:
                dresp = client.get(detail_url, headers=HEADERS, follow_redirects=True, timeout=15)
                if dresp.status_code != 200:
                    continue
            except Exception:
                continue

            dhtml = dresp.text

            # Title
            title_m = re.search(r'<h1[^>]*>(.*?)</h1>', dhtml, re.DOTALL)
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else slug.replace("-", " ").title()

            # Screenshot
            og_m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', dhtml)
            img_url = og_m.group(1) if og_m else None
            if not img_url:
                continue

            ext = get_extension(img_url)
            filepath = ss_dir / f"{slug}.{ext}"
            if not download_image(client, img_url, filepath):
                continue

            # Tags
            tag_matches = re.findall(r'/websites/([a-z0-9-]+)/"', dhtml)
            tags = ["awwwards", "sotd", "award-winning"] + list(set(tag_matches))[:5]

            pattern = DesignPattern(
                id=pid, name=title[:100], source="awwwards",
                source_url=detail_url, image_url=img_url,
                page_type="Landing Page", platform=Platform.WEB,
                visual_style=["Editorial"], quality_score=7.5,
                tags=tags
            )
            new_patterns.append(pattern.model_dump())
            existing_ids.add(pid)
            print(f"    ✓ [{len(new_patterns)}] {title[:50]}", flush=True)
            time.sleep(0.8)

        time.sleep(1.5)

    print(f"  Awwwards total: {len(new_patterns)} new", flush=True)
    return new_patterns


# =============================================================
# SOURCE 2: LAND-BOOK (categories)
# =============================================================
def scrape_landbook(client, existing_ids, max_count=300):
    """Scrape Land-book design gallery by category."""
    print(f"\n{'='*60}", flush=True)
    print("SOURCE: LAND-BOOK", flush=True)
    print(f"{'='*60}", flush=True)

    ss_dir = SCREENSHOTS_DIR / "landbook"
    ss_dir.mkdir(parents=True, exist_ok=True)
    new_patterns = []

    categories = [
        ("landing-page", "Landing Page"),
        ("portfolio", "Profile"),
        ("ecommerce", "Product Page"),
        ("pricing-page", "Pricing"),
        ("blog", "Blog Post"),
        ("about-us-page", "Landing Page"),
        ("sign-up-page", "Signup"),
        ("career-page", "Landing Page"),
        ("case-study", "Landing Page"),
        ("product-page", "Product Page"),
    ]

    for cat_slug, page_type in categories:
        if len(new_patterns) >= max_count:
            break

        for page in range(1, 6):  # 5 pages per category
            if len(new_patterns) >= max_count:
                break

            url = f"https://land-book.com/design/{cat_slug}?page={page}"
            print(f"  {cat_slug} p{page}...", flush=True)

            try:
                resp = client.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
                if resp.status_code != 200:
                    print(f"    [{resp.status_code}]", flush=True)
                    break
            except Exception as e:
                print(f"    [ERROR] {e}", flush=True)
                break

            html = resp.text
            # Extract website links
            site_links = re.findall(r'/websites/(\d+)-([a-z0-9-]+)', html)
            if not site_links:
                break

            seen = set()
            for site_id, site_slug in site_links:
                if len(new_patterns) >= max_count:
                    break
                if site_id in seen:
                    continue
                seen.add(site_id)

                pid = f"landbook-{site_id}"
                if pid in existing_ids:
                    continue

                # Get detail page for screenshot
                detail_url = f"https://land-book.com/websites/{site_id}-{site_slug}"
                try:
                    dresp = client.get(detail_url, headers=HEADERS, follow_redirects=True, timeout=15)
                    if dresp.status_code != 200:
                        continue
                except Exception:
                    continue

                dhtml = dresp.text
                og_m = re.search(r'<meta\s+(?:property|name)="og:image"\s+content="([^"]+)"', dhtml)
                if not og_m:
                    og_m = re.search(r'<meta\s+content="([^"]+)"\s+(?:property|name)="og:image"', dhtml)
                img_url = og_m.group(1) if og_m else None
                if not img_url:
                    continue

                title_m = re.search(r'<h1[^>]*>(.*?)</h1>', dhtml, re.DOTALL)
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else site_slug.replace("-", " ").title()

                ext = get_extension(img_url)
                filepath = ss_dir / f"{site_id}-{site_slug[:40]}.{ext}"
                if not download_image(client, img_url, filepath):
                    continue

                tags = ["landbook", cat_slug]
                pattern = DesignPattern(
                    id=pid, name=title[:100], source="landbook",
                    source_url=detail_url, image_url=img_url,
                    page_type=page_type, platform=Platform.WEB,
                    visual_style=["Minimal"], quality_score=6.0,
                    tags=tags
                )
                new_patterns.append(pattern.model_dump())
                existing_ids.add(pid)
                print(f"    ✓ [{len(new_patterns)}] {title[:50]}", flush=True)
                time.sleep(0.8)

            time.sleep(1)

    print(f"  Land-book total: {len(new_patterns)} new", flush=True)
    return new_patterns


# =============================================================
# SOURCE 3: CURATED TOP SAAS/PRODUCT SITES
# =============================================================
def scrape_curated_sites(client, existing_ids, max_count=130):
    """Get screenshots from top SaaS and product websites via og:image."""
    print(f"\n{'='*60}", flush=True)
    print("SOURCE: CURATED TOP SITES", flush=True)
    print(f"{'='*60}", flush=True)

    ss_dir = SCREENSHOTS_DIR / "curated"
    ss_dir.mkdir(parents=True, exist_ok=True)
    new_patterns = []

    # Top SaaS, product, and design-forward sites
    sites = [
        # SaaS / Dev Tools
        ("https://linear.app", "Linear", "Dashboard", "Productivity", ["Minimal"]),
        ("https://vercel.com", "Vercel", "Landing Page", "Developer Tools", ["Minimal", "Monochrome"]),
        ("https://stripe.com", "Stripe", "Landing Page", "Fintech", ["Minimal", "Corporate"]),
        ("https://notion.so", "Notion", "Landing Page", "Productivity", ["Minimal"]),
        ("https://figma.com", "Figma", "Landing Page", "Developer Tools", ["Playful"]),
        ("https://supabase.com", "Supabase", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://planetscale.com", "PlanetScale", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://railway.app", "Railway", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://arc.net", "Arc Browser", "Landing Page", "Productivity", ["Minimal"]),
        ("https://raycast.com", "Raycast", "Landing Page", "Productivity", ["Minimal"]),
        ("https://cal.com", "Cal.com", "Landing Page", "Productivity", ["Minimal"]),
        ("https://resend.com", "Resend", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://clerk.com", "Clerk", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://neon.tech", "Neon", "Landing Page", "Developer Tools", ["Gradient-Heavy"]),
        ("https://turso.tech", "Turso", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://convex.dev", "Convex", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://upstash.com", "Upstash", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://dub.co", "Dub", "Landing Page", "SaaS", ["Minimal"]),
        ("https://cal.com/pricing", "Cal.com Pricing", "Pricing", "Productivity", ["Minimal"]),
        ("https://midday.ai", "Midday", "Landing Page", "Fintech", ["Minimal"]),
        ("https://liveblocks.io", "Liveblocks", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://trigger.dev", "Trigger.dev", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://inngest.com", "Inngest", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://highlight.io", "Highlight", "Landing Page", "Developer Tools", ["Gradient-Heavy"]),
        ("https://loops.so", "Loops", "Landing Page", "SaaS", ["Minimal"]),
        ("https://plain.com", "Plain", "Landing Page", "SaaS", ["Minimal"]),
        ("https://typefully.com", "Typefully", "Landing Page", "Social Media", ["Minimal"]),
        # E-commerce / Consumer
        ("https://www.apple.com", "Apple", "Landing Page", "E-Commerce", ["Minimal", "Luxury"]),
        ("https://www.tesla.com", "Tesla", "Landing Page", "E-Commerce", ["Minimal", "Futuristic"]),
        ("https://www.airbnb.com", "Airbnb", "Landing Page", "Travel", ["Minimal"]),
        ("https://www.spotify.com", "Spotify", "Landing Page", "Entertainment", ["Gradient-Heavy"]),
        ("https://www.duolingo.com", "Duolingo", "Landing Page", "Education", ["Playful"]),
        ("https://www.canva.com", "Canva", "Landing Page", "Productivity", ["Playful"]),
        ("https://www.framer.com", "Framer", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://webflow.com", "Webflow", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://www.squarespace.com", "Squarespace", "Landing Page", "SaaS", ["Editorial"]),
        ("https://www.shopify.com", "Shopify", "Landing Page", "E-Commerce", ["Corporate"]),
        ("https://www.wise.com", "Wise", "Landing Page", "Fintech", ["Minimal"]),
        ("https://www.revolut.com", "Revolut", "Landing Page", "Fintech", ["Futuristic"]),
        ("https://monzo.com", "Monzo", "Landing Page", "Fintech", ["Playful"]),
        ("https://mercury.com", "Mercury", "Landing Page", "Fintech", ["Minimal"]),
        ("https://ramp.com", "Ramp", "Landing Page", "Fintech", ["Minimal"]),
        ("https://brex.com", "Brex", "Landing Page", "Fintech", ["Minimal"]),
        # Design-forward
        ("https://www.awwwards.com", "Awwwards", "Landing Page", None, ["Editorial"]),
        ("https://www.behance.net", "Behance", "Landing Page", None, ["Minimal"]),
        ("https://dribbble.com", "Dribbble", "Landing Page", None, ["Playful"]),
        ("https://layers.to", "Layers", "Landing Page", None, ["Minimal"]),
        ("https://godly.website", "Godly", "Landing Page", None, ["Minimal"]),
        # AI / ML
        ("https://openai.com", "OpenAI", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://anthropic.com", "Anthropic", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://huggingface.co", "Hugging Face", "Landing Page", "Developer Tools", ["Playful"]),
        ("https://replicate.com", "Replicate", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://together.ai", "Together AI", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://www.perplexity.ai", "Perplexity", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://cursor.com", "Cursor", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://v0.dev", "v0", "Landing Page", "Developer Tools", ["Minimal"]),
        # Health / Wellness
        ("https://www.headspace.com", "Headspace", "Landing Page", "Health & Wellness", ["Playful", "Organic"]),
        ("https://www.calm.com", "Calm", "Landing Page", "Health & Wellness", ["Organic"]),
        ("https://www.whoop.com", "Whoop", "Landing Page", "Health & Wellness", ["Futuristic"]),
        # Misc quality
        ("https://www.loom.com", "Loom", "Landing Page", "Productivity", ["Minimal"]),
        ("https://www.pitch.com", "Pitch", "Landing Page", "Productivity", ["Playful"]),
        ("https://www.miro.com", "Miro", "Landing Page", "Productivity", ["Playful"]),
        ("https://www.airtable.com", "Airtable", "Landing Page", "Productivity", ["Corporate"]),
        ("https://www.monday.com", "Monday.com", "Landing Page", "Productivity", ["Playful"]),
        ("https://slack.com", "Slack", "Landing Page", "Productivity", ["Playful"]),
        ("https://discord.com", "Discord", "Landing Page", "Social Media", ["Playful"]),
        ("https://www.twitch.tv", "Twitch", "Landing Page", "Entertainment", ["Futuristic"]),
        ("https://github.com", "GitHub", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://gitlab.com", "GitLab", "Landing Page", "Developer Tools", ["Corporate"]),
        ("https://www.atlassian.com", "Atlassian", "Landing Page", "Productivity", ["Corporate"]),
        ("https://1password.com", "1Password", "Landing Page", "SaaS", ["Minimal"]),
        ("https://tailwindcss.com", "Tailwind CSS", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://nextjs.org", "Next.js", "Landing Page", "Developer Tools", ["Minimal", "Monochrome"]),
        ("https://remix.run", "Remix", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://astro.build", "Astro", "Landing Page", "Developer Tools", ["Playful"]),
        ("https://svelte.dev", "Svelte", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://vuejs.org", "Vue.js", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://laravel.com", "Laravel", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://www.prisma.io", "Prisma", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://drizzle.team", "Drizzle", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://pnpm.io", "pnpm", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://bun.sh", "Bun", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://deno.com", "Deno", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://biomejs.dev", "Biome", "Landing Page", "Developer Tools", ["Minimal"]),
        ("https://www.radix-ui.com", "Radix UI", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://ui.shadcn.com", "shadcn/ui", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://chakra-ui.com", "Chakra UI", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://headlessui.com", "Headless UI", "Documentation", "Developer Tools", ["Minimal"]),
        ("https://www.tremor.so", "Tremor", "Documentation", "Developer Tools", ["Minimal"]),
        # Food / Delivery
        ("https://www.doordash.com", "DoorDash", "Landing Page", "Food & Delivery", ["Corporate"]),
        ("https://www.uber.com", "Uber", "Landing Page", "Travel", ["Minimal"]),
        # Real Estate
        ("https://www.zillow.com", "Zillow", "Landing Page", "Real Estate", ["Corporate"]),
        ("https://www.redfin.com", "Redfin", "Landing Page", "Real Estate", ["Corporate"]),
        # Education
        ("https://www.coursera.org", "Coursera", "Landing Page", "Education", ["Corporate"]),
        ("https://www.udemy.com", "Udemy", "Landing Page", "Education", ["Corporate"]),
        ("https://brilliant.org", "Brilliant", "Landing Page", "Education", ["Playful"]),
    ]

    for site_url, name, page_type, industry, styles in sites:
        if len(new_patterns) >= max_count:
            break

        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        pid = f"curated-{slug}"
        if pid in existing_ids:
            continue

        try:
            resp = client.get(site_url, headers=HEADERS, follow_redirects=True, timeout=15)
            if resp.status_code != 200:
                print(f"  [{resp.status_code}] {name}", flush=True)
                continue
        except Exception as e:
            print(f"  [ERROR] {name}: {e}", flush=True)
            continue

        html = resp.text

        # Get og:image
        og_m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        if not og_m:
            og_m = re.search(r'<meta\s+content="([^"]+)"\s+property="og:image"', html)
        img_url = og_m.group(1) if og_m else None

        if img_url and not img_url.startswith("http"):
            img_url = urljoin(site_url, img_url)

        if not img_url:
            continue

        ext = get_extension(img_url)
        filepath = ss_dir / f"{slug}.{ext}"
        if not download_image(client, img_url, filepath):
            continue

        # Check file size (quality gate)
        if filepath.stat().st_size < 10000:  # Less than 10KB = probably garbage
            filepath.unlink()
            continue

        tags = ["curated", slug]
        if industry:
            tags.append(industry.lower().replace(" & ", "-").replace(" ", "-"))

        pattern = DesignPattern(
            id=pid, name=name, source="curated",
            source_url=site_url, image_url=img_url,
            page_type=page_type, industry=industry,
            platform=Platform.WEB,
            visual_style=styles, quality_score=8.0,
            tags=tags
        )
        new_patterns.append(pattern.model_dump())
        existing_ids.add(pid)
        print(f"  ✓ [{len(new_patterns)}] {name}", flush=True)
        time.sleep(0.5)

    print(f"  Curated total: {len(new_patterns)} new", flush=True)
    return new_patterns


# =============================================================
# MAIN
# =============================================================
def main():
    existing = load_existing()
    existing_ids = {p["id"] for p in existing}
    print(f"Starting with {len(existing)} patterns\n", flush=True)

    client = httpx.Client(timeout=20)
    all_new = []

    # Source 1: Curated top sites (fastest, most reliable)
    curated = scrape_curated_sites(client, existing_ids)
    all_new.extend(curated)

    # Source 2: Awwwards
    awwwards = scrape_awwwards(client, existing_ids)
    all_new.extend(awwwards)

    # Source 3: Land-book
    landbook = scrape_landbook(client, existing_ids)
    all_new.extend(landbook)

    client.close()

    # Save all
    if all_new:
        total = save_patterns(existing, all_new)
        print(f"\n{'='*60}", flush=True)
        print(f"TOTAL NEW: {len(all_new)}", flush=True)
        print(f"  Curated: {len(curated)}", flush=True)
        print(f"  Awwwards: {len(awwwards)}", flush=True)
        print(f"  Land-book: {len(landbook)}", flush=True)
        print(f"DB total: {total}", flush=True)
    else:
        print("\nNo new patterns collected.", flush=True)

    # Screenshot quality report
    print(f"\n{'='*60}", flush=True)
    print("SCREENSHOT REPORT", flush=True)
    for subdir in SCREENSHOTS_DIR.iterdir():
        if subdir.is_dir():
            files = list(subdir.glob("*"))
            sizes = [f.stat().st_size for f in files if f.is_file()]
            if sizes:
                avg_kb = sum(sizes) / len(sizes) / 1024
                print(f"  {subdir.name}: {len(files)} files, avg {avg_kb:.0f}KB", flush=True)


if __name__ == "__main__":
    main()
