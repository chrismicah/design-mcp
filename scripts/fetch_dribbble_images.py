"""Download Dribbble design screenshots from CDN URLs."""
import httpx
import os
import time
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# High-res image URLs from Dribbble CDN (extracted via browser)
IMAGES = [
    ("26565558-ai-dashboard.webp", "https://cdn.dribbble.com/userupload/45035924/file/a8cc40ee82334cd8025cf98b388eb597.png?crop=96x72-3105x2329&format=webp&resize=1600x&vertical=center"),
    ("24468365-project-monitoring.webp", "https://cdn.dribbble.com/userupload/15442924/file/original-b0f3541c72d6b872e8fe87cb54166965.png?format=webp&resize=1600x&vertical=center"),
    ("25770479-sales-analytics-dark.webp", "https://cdn.dribbble.com/userupload/42125185/file/original-d465687c21d4f5d26a35d41d1dfbedfc.png?format=webp&resize=1600x&vertical=center"),
    ("25541330-shown-ai-dashboard.webp", "https://cdn.dribbble.com/userupload/19423451/file/original-8b2bbb8467fefee1e420678a1cc1c4cb.png?crop=0x0-4800x3600&format=webp&resize=1600x&vertical=center"),
    ("25477618-coinstax-crypto.webp", "https://cdn.dribbble.com/userupload/18446865/file/original-9780e96cd7d7a0b2d22eb6ed653cba2c.png?format=webp&resize=1600x&vertical=center"),
    ("26123474-crypto-dashboard.webp", "https://cdn.dribbble.com/userupload/43623845/file/original-3268178b691d0b059b7f88eadcb14d53.png?format=webp&resize=1600x&vertical=center"),
    ("22079049-botly-chatbot-dark.webp", "https://cdn.dribbble.com/userupload/8787676/file/original-c8984c5f629f8ee60f8d58ab19738720.png?resize=1600x&vertical=center"),
    ("16971369-manycrypto-dark.webp", "https://cdn.dribbble.com/users/702789/screenshots/16971369/media/7df0d3b40bc7edfb0b2bd810db8fbc38.png?resize=1600x&vertical=center"),
    ("18356550-task-management-dark.webp", "https://cdn.dribbble.com/users/2170960/screenshots/18356550/media/ef97f6d3c34b7f7daada0bccc437eb96.png?resize=1600x&vertical=center"),
    ("25748099-user-management.webp", "https://cdn.dribbble.com/userupload/18173098/file/original-39e8b2df3f18cc7de2c18c7bd59cfa2f.png?format=webp&resize=1600x&vertical=center"),
]

def download_all():
    success = 0
    with httpx.Client(follow_redirects=True, timeout=30) as client:
        for filename, url in IMAGES:
            filepath = SCREENSHOT_DIR / filename
            if filepath.exists():
                print(f"  Skip (exists): {filename}")
                success += 1
                continue
            try:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    filepath.write_bytes(resp.content)
                    print(f"  OK: {filename} ({len(resp.content)//1024}KB)")
                    success += 1
                else:
                    print(f"  FAIL: {filename} (status={resp.status_code}, size={len(resp.content)})")
            except Exception as e:
                print(f"  ERR: {filename}: {e}")
            time.sleep(0.5)

    print(f"\nDownloaded {success}/{len(IMAGES)} Dribbble screenshots")

if __name__ == "__main__":
    download_all()
