# Dribbble Scraping — Playwriter MCP Instructions

## Search Keywords (run each one)
Combine page types with modifiers:
- "dashboard dark mode"
- "pricing page SaaS"
- "onboarding fintech"
- "settings page minimal"
- "checkout ecommerce"
- "landing page startup"
- "404 page creative"
- "login glassmorphism"
- "admin panel analytics"
- "profile page mobile"
- "file explorer desktop"
- "chat interface modern"
- "kanban board productivity"
- "notification center"
- "empty state illustration"

## For Each Search
1. Navigate to `https://dribbble.com/search/{keyword}`
2. Wait for results grid to load
3. For each shot in the first 2 pages (24-48 results per keyword):
   - Extract: title, image URL (from `img` src), shot URL, designer name
   - Click into shot detail page
   - Extract: tags (from tag links), description text, any tool/technology mentions
4. Map to DesignPattern:
   - `page_type`: Infer from title + tags
   - `visual_style`: Infer from tags (look for "minimal", "dark", "glassmorphism", etc.)
   - `ui_elements`: Infer from tags and description
   - `industry`: Infer from tags and description
   - `color_mode`: Infer from image brightness or tags
5. Append to data/patterns.json

## Rate Limiting
- Wait 2-3 seconds between page navigations
- If blocked or rate limited, pause for 60 seconds and retry
- Target: ~500 patterns from Dribbble
