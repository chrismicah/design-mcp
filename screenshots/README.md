# Screenshots

This directory contains high-resolution design screenshots used as visual references for the design patterns database.

## What's Included in Git

Only a small sample set is committed to keep the repo lightweight (~39 files):

- `dribbble/` — 7 reference screenshots (original curated samples)
- `awwwards/` — 31 reference screenshots (SOTD winners)

## Downloading the Full Set (~600MB)

The bulk screenshots are gitignored. To download the full collection:

```bash
# From the project root
python scripts/download_all_screenshots.py
```

This will populate:
- `screenshots/dribbble/` — 284 shots from Dribbble popular pages
- `screenshots/awwwards/` — 300 shots from Awwwards SOTD winners
- `screenshots/curated/` — 68 shots from top SaaS products
- `screenshots/landbook/` — 90 shots from landing page galleries

## Quality

All screenshots are high-resolution (1600px+ wide) and filtered for quality (>50KB minimum file size).
