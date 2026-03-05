"""
Take high-res screenshots of top design websites.
Uses httpx to download from screenshot APIs or direct CDN.
"""
import httpx
import time
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "curated"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Top sites for design inspiration - direct screenshot URLs from various sources
# These are well-known product websites with excellent UI design
TOP_SITES = [
    # SaaS Dashboards
    ("linear-app", "https://linear.app"),
    ("notion-home", "https://www.notion.com"),
    ("figma-home", "https://www.figma.com"),
    ("stripe-home", "https://stripe.com"),
    ("vercel-home", "https://vercel.com"),
    ("railway-home", "https://railway.app"),
    ("supabase-home", "https://supabase.com"),
    ("clerk-home", "https://clerk.com"),
    ("resend-home", "https://resend.com"),
    ("cal-home", "https://cal.com"),
    # Creative / Agency
    ("framer-home", "https://www.framer.com"),
    ("webflow-home", "https://webflow.com"),
    ("spline-home", "https://spline.design"),
    ("rive-home", "https://rive.app"),
    ("lottiefiles-home", "https://lottiefiles.com"),
    # Fintech
    ("mercury-home", "https://mercury.com"),
    ("ramp-home", "https://ramp.com"),
    ("brex-home", "https://www.brex.com"),
    ("wise-home", "https://wise.com"),
    ("revolut-home", "https://www.revolut.com"),
    # E-commerce
    ("shopify-home", "https://www.shopify.com"),
    ("gumroad-home", "https://gumroad.com"),
    ("lemonsqueezy-home", "https://www.lemonsqueezy.com"),
    # Developer tools
    ("github-home", "https://github.com"),
    ("gitlab-home", "https://about.gitlab.com"),
    ("planetscale-home", "https://planetscale.com"),
    ("neon-home", "https://neon.tech"),
    ("turso-home", "https://turso.tech"),
    # Productivity
    ("todoist-home", "https://todoist.com"),
    ("cron-home", "https://cron.com"),
    ("height-home", "https://height.app"),
    ("arc-home", "https://arc.net"),
    ("raycast-home", "https://www.raycast.com"),
    # AI
    ("anthropic-home", "https://www.anthropic.com"),
    ("openai-home", "https://openai.com"),
    ("midjourney-home", "https://www.midjourney.com"),
    ("replicate-home", "https://replicate.com"),
    ("huggingface-home", "https://huggingface.co"),
]

def screenshot_via_api(name: str, url: str, client: httpx.Client) -> bool:
    """Use a free screenshot API."""
    filepath = SCREENSHOT_DIR / f"{name}.png"
    if filepath.exists() and filepath.stat().st_size > 50000:
        return True  # Already exists
    
    # Use microlink API (free tier)
    api_url = f"https://api.microlink.io/?url={url}&screenshot=true&meta=false&embed=screenshot.url"
    try:
        resp = client.get(api_url)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success" and data.get("data", {}).get("screenshot", {}).get("url"):
                img_url = data["data"]["screenshot"]["url"]
                img_resp = client.get(img_url)
                if img_resp.status_code == 200 and len(img_resp.content) > 50000:
                    filepath.write_bytes(img_resp.content)
                    return True
    except Exception:
        pass
    return False


def main():
    print(f"Taking screenshots of {len(TOP_SITES)} top design sites...", flush=True)
    
    success = 0
    skipped = 0
    failed = 0
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    with httpx.Client(follow_redirects=True, timeout=60, headers=headers) as client:
        for i, (name, url) in enumerate(TOP_SITES):
            filepath = SCREENSHOT_DIR / f"{name}.png"
            if filepath.exists() and filepath.stat().st_size > 50000:
                skipped += 1
                print(f"  [{i+1}/{len(TOP_SITES)}] SKIP: {name}", flush=True)
                continue
            
            ok = screenshot_via_api(name, url, client)
            if ok:
                success += 1
                print(f"  [{i+1}/{len(TOP_SITES)}] OK: {name}", flush=True)
            else:
                failed += 1
                print(f"  [{i+1}/{len(TOP_SITES)}] FAIL: {name}", flush=True)
            
            time.sleep(1.5)  # Rate limit
    
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Failed: {failed}")
    print(f"Total curated screenshots: {len(list(SCREENSHOT_DIR.glob('*')))}", flush=True)


if __name__ == "__main__":
    main()
