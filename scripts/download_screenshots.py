"""
Download design screenshots from Dribbble CDN URLs.
Saves to screenshots/dribbble/ with shot ID as filename.
"""
import httpx
import asyncio
import os
import re
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Top Dribbble shots to download (high engagement ones)
SHOTS = {
    "task-management-dark-260k": "https://cdn.dribbble.com/userupload/4177076/file/original-1c889f3c08e7e7efb tried.png",
    # We'll populate these from browser extraction
}


async def download_image(client: httpx.AsyncClient, url: str, filename: str) -> bool:
    """Download a single image."""
    filepath = SCREENSHOT_DIR / filename
    if filepath.exists():
        return True
    try:
        resp = await client.get(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1000:
            filepath.write_bytes(resp.content)
            print(f"  Downloaded: {filename} ({len(resp.content)//1024}KB)")
            return True
        else:
            print(f"  Failed: {filename} (status={resp.status_code})")
            return False
    except Exception as e:
        print(f"  Error: {filename}: {e}")
        return False


async def download_batch(urls: dict[str, str]):
    """Download a batch of images."""
    async with httpx.AsyncClient() as client:
        tasks = [download_image(client, url, name) for name, url in urls.items()]
        results = await asyncio.gather(*tasks)
        success = sum(1 for r in results if r)
        print(f"Downloaded {success}/{len(urls)} images")


if __name__ == "__main__":
    # Test with known URLs
    test_urls = {
        "botly-dashboard-dark.png": "https://cdn.dribbble.com/userupload/8787676/file/original-c8984c5f629f8ee60f8d58ab19738720.png?resize=1200x&vertical=center",
    }
    asyncio.run(download_batch(test_urls))
