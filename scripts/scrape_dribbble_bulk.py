"""
Bulk download Dribbble high-res screenshots.
URLs collected via browser automation from multiple categories.
"""
import httpx
import time
import hashlib
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# High-res CDN URLs collected from Dribbble popular pages
URLS = []

def load_urls(filepath):
    """Load URLs from a text file (one per line)."""
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip() and line.strip().startswith('http')]

def download_all(url_file):
    urls = load_urls(url_file)
    print(f"Downloading {len(urls)} Dribbble screenshots...")
    
    success = 0
    skipped = 0
    failed = 0
    
    with httpx.Client(
        follow_redirects=True, 
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    ) as client:
        for i, url in enumerate(urls):
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            ext = "webp" if "format=webp" in url else "png"
            filename = f"dribbble-{url_hash}.{ext}"
            filepath = SCREENSHOT_DIR / filename
            
            if filepath.exists() and filepath.stat().st_size > 10000:
                skipped += 1
                continue
            
            try:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    filepath.write_bytes(resp.content)
                    size_kb = len(resp.content) // 1024
                    print(f"  [{i+1}/{len(urls)}] OK: {filename} ({size_kb}KB)", flush=True)
                    success += 1
                else:
                    print(f"  [{i+1}/{len(urls)}] FAIL: status={resp.status_code}, size={len(resp.content)}", flush=True)
                    failed += 1
            except Exception as e:
                print(f"  [{i+1}/{len(urls)}] ERR: {e}", flush=True)
                failed += 1
            
            time.sleep(0.3)  # Be nice to CDN
    
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Failed: {failed}")
    print(f"Total Dribbble screenshots: {len(list(SCREENSHOT_DIR.glob('*')))}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        download_all(sys.argv[1])
    else:
        print("Usage: python scrape_dribbble_bulk.py <urls_file>")
