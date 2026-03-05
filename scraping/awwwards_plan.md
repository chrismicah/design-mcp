# Awwwards Scraping — Playwriter MCP Instructions

## Strategy
Awwwards is best for cutting-edge web design. Focus on award winners.

1. Navigate to `https://www.awwwards.com/websites/`
2. Use filters: technology (React, Vue), style, type
3. For each site entry:
   - Extract: site name, URL, technology tags, categories
   - Extract: design scores (if visible)
   - Take note of the screenshot/thumbnail URL
4. Map to DesignPattern:
   - `visual_style`: from Awwwards' style tags
   - `platform`: always "web"
   - `quality_score`: map from Awwwards scores (normalize to 0-10)
5. Append to data/patterns.json

## Rate Limiting
- Wait 2-3 seconds between pages
- Target: ~300 patterns from Awwwards
