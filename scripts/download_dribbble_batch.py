"""
Download Dribbble screenshots from collected CDN URLs.
Filters out videos, deduplicates, and downloads high-res images.
"""
import httpx
import hashlib
import time
import re
import sys
from pathlib import Path
from html import unescape

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Categories to scrape
DRIBBBLE_PAGES = [
    "https://dribbble.com/shots/popular/web-design",
    "https://dribbble.com/shots/popular/web-design?page=2",
    "https://dribbble.com/shots/popular/web-design?page=3",
    "https://dribbble.com/shots/popular/web-design?page=4",
    "https://dribbble.com/shots/popular/web-design?page=5",
    "https://dribbble.com/shots/popular/web-design?page=6",
    "https://dribbble.com/shots/popular/web-design?page=7",
    "https://dribbble.com/shots/popular/web-design?page=8",
    "https://dribbble.com/shots/popular/web-design?page=9",
    "https://dribbble.com/shots/popular/web-design?page=10",
    "https://dribbble.com/shots/popular/product-design",
    "https://dribbble.com/shots/popular/product-design?page=2",
    "https://dribbble.com/shots/popular/product-design?page=3",
    "https://dribbble.com/shots/popular/product-design?page=4",
    "https://dribbble.com/shots/popular/product-design?page=5",
    "https://dribbble.com/shots/popular/mobile",
    "https://dribbble.com/shots/popular/mobile?page=2",
    "https://dribbble.com/shots/popular/mobile?page=3",
    "https://dribbble.com/tags/dashboard",
    "https://dribbble.com/tags/dashboard?page=2",
    "https://dribbble.com/tags/landing-page",
    "https://dribbble.com/tags/landing-page?page=2",
    "https://dribbble.com/tags/saas",
    "https://dribbble.com/tags/saas?page=2",
    "https://dribbble.com/tags/fintech",
    "https://dribbble.com/tags/ecommerce",
]


def extract_image_urls(html: str) -> set:
    """Extract unique high-res image URLs from Dribbble page HTML."""
    urls = set()
    
    # Match CDN URLs for userupload images
    pattern = r'cdn\.dribbble\.com/userupload/\d+/file/[^"\'<>\s]+'
    matches = re.findall(pattern, html)
    
    for m in matches:
        url = 'https://' + unescape(m)
        
        # Skip videos and avatars
        if any(x in url for x in ['.mp4', 'avatars', 'small-', 'large-', '{width}']):
            continue
        
        # Only keep image files
        if not any(ext in url for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
            continue
        
        # Convert to high-res
        url = re.sub(r'resize=\d+x\d*', 'resize=1600x', url)
        url = re.sub(r'crop=[^&]+&', '', url)
        
        # Deduplicate by file ID (extract unique part)
        urls.add(url)
    
    return urls


def deduplicate_by_file(urls: set) -> list:
    """Keep only one URL per unique file."""
    seen_files = {}
    for url in urls:
        # Extract the file hash part
        match = re.search(r'/file/([a-f0-9]+)', url)
        if match:
            file_id = match.group(1)
            if file_id not in seen_files:
                # Prefer webp format
                seen_files[file_id] = url
            elif 'format=webp' in url and 'format=webp' not in seen_files[file_id]:
                seen_files[file_id] = url
    return list(seen_files.values())


def main():
    print("Scraping Dribbble CDN URLs from category pages...", flush=True)
    
    all_urls = set()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }
    
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        for i, page_url in enumerate(DRIBBBLE_PAGES):
            try:
                resp = client.get(page_url)
                if resp.status_code == 200:
                    urls = extract_image_urls(resp.text)
                    all_urls.update(urls)
                    print(f"  [{i+1}/{len(DRIBBBLE_PAGES)}] {page_url.split('/')[-1]}: +{len(urls)} (total: {len(all_urls)})", flush=True)
                else:
                    print(f"  [{i+1}/{len(DRIBBBLE_PAGES)}] SKIP: status {resp.status_code}", flush=True)
            except Exception as e:
                print(f"  [{i+1}/{len(DRIBBBLE_PAGES)}] ERR: {e}", flush=True)
            time.sleep(0.5)
    
    # Deduplicate
    unique_urls = deduplicate_by_file(all_urls)
    print(f"\nTotal unique images: {len(unique_urls)}", flush=True)
    
    # Download
    print(f"\nDownloading {len(unique_urls)} high-res Dribbble screenshots...", flush=True)
    success = 0
    skipped = 0
    failed = 0
    
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        for i, url in enumerate(unique_urls):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            if '.jpg' in url or '.jpeg' in url:
                ext = 'jpg'
            elif '.webp' in url:
                ext = 'webp'
            else:
                ext = 'png'
            
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
                    success += 1
                    if success % 20 == 0:
                        print(f"  Downloaded {success} so far... ({size_kb}KB latest)", flush=True)
                else:
                    failed += 1
            except Exception as e:
                failed += 1
            
            time.sleep(0.2)
    
    total_files = len(list(SCREENSHOT_DIR.glob('*')))
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Failed: {failed}")
    print(f"Total Dribbble screenshots: {total_files}", flush=True)


if __name__ == "__main__":
    main()
