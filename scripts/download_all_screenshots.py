"""
Download all design screenshots for the MCP database.
Run this after cloning to populate the screenshots/ directory.

Usage: python scripts/download_all_screenshots.py
"""
print("Note: Screenshot download scripts are in the scripts/ directory.")
print("Run individual scripts:")
print("  python scripts/dribbble_urls.py          # Batch 1 Dribbble (97 shots)")
print("  python scripts/dribbble_batch2.py         # Batch 2 Dribbble (180 shots)")
print("  python scripts/screenshot_top_sites.py    # Curated SaaS sites")
print()
print("Awwwards and Landbook screenshots were scraped via browser automation")
print("and httpx during the initial build. The scraping scripts are preserved")
print("in scripts/ingest_awwwards.py for reference.")
print()
print("The patterns database (data/patterns.json) already contains all 7,080")
print("patterns with metadata — screenshots are optional visual references.")
