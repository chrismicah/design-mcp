# Screenshots (Optional)

This directory contains **742 high-resolution design screenshots** used to build the patterns database.

**You don't need these to use the MCP.** The server runs entirely off `data/patterns.json`, which already contains all extracted design intelligence (page types, colors, layouts, UI elements, quality scores).

## When you'd want them

- Browsing source designs for visual inspiration
- Re-running vision analysis to update `data/vision_results.json`
- Adding new screenshots and re-building the database

## How to download

Screenshots are stored in Git LFS. After cloning:

```bash
git lfs pull
```

This downloads all 742 screenshots (~600 MB).

## Contents

| Directory | Files | Size | Source |
|-----------|-------|------|--------|
| `awwwards/` | 300 | 312 MB | Site of the Day winners |
| `dribbble/` | 284 | 260 MB | Popular web design shots |
| `curated/` | 68 | 24 MB | Top SaaS products (Stripe, Linear, etc.) |
| `landbook/` | 90 | 6 MB | Landing page gallery |
