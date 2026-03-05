# Design Intelligence MCP Server

An MCP (Model Context Protocol) server that gives AI agents structured access to **7,000+ real-world design patterns** for higher-quality UI generation.

Instead of hallucinating layouts and guessing at component structures, AI agents can search proven design patterns, get semantic tokens, and understand behavioral specifications before generating code.

## Why This Exists

Research shows that LLMs generate significantly better UI code when given:
- **Explicit layout types** (prevents absolute positioning hallucination)
- **Behavioral descriptions** (how patterns work, not just how they look)
- **Semantic tokens** (avoids magic numbers and hardcoded colors)
- **Component structure hints** (prevents hallucinated prop interfaces)
- **Accessibility notes** (60% reduction in inaccessibility issues)

This MCP server provides all of that from a curated database of real-world examples.

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install fastmcp pydantic httpx uvicorn
```

### 2. Connect to Claude Desktop

Add to `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "design-intelligence": {
      "command": "python",
      "args": ["C:\\path\\to\\design-mcp\\server.py"]
    }
  }
}
```

### 3. Connect to Cursor

Settings → MCP Servers → Add:
- Name: `design-intelligence`
- Command: `python /path/to/design-mcp/server.py`

### 4. Use It

Ask your AI agent things like:
- *"Search for dark mode dashboard designs in fintech"*
- *"Show me pricing page patterns with glassmorphism"*
- *"Get the behavioral spec for empty states"*
- *"Compare how different products handle onboarding"*

## MCP Tools

### `search_design_patterns`
Search 7,000+ design patterns with filters for page type, industry, platform, color mode, and visual style.

```python
# Example: Find fintech dashboards
results = await search_design_patterns(
    query="analytics dashboard",
    page_type="Dashboard",
    industry="Fintech",
    color_mode="dark",
    limit=5
)
```

### `get_design_blueprint`
Get the full blueprint for a specific pattern, including layout info, component hints, behavioral descriptions, and accessibility notes.

### `get_semantic_tokens`
Get W3C-format semantic design tokens for consistent styling — colors, spacing, typography, borders.

### `get_design_taxonomy`
Browse the full taxonomy: 25 page types, 25 UX patterns, 47 UI elements, 15 industries, 16 visual styles.

### `get_behavioral_pattern`
Get behavioral specs for common UX patterns: empty states, skeleton loading, error handling, onboarding flows, form validation, infinite scroll, command palettes.

### `compare_design_approaches`
Compare how different products handle the same page type — side-by-side blueprints with a summary of key differences.

## Data Sources

| Source | Patterns | Description |
|--------|----------|-------------|
| webui-7kbal | 6,134 | HuggingFace dataset — HTML, CSS, accessibility trees from 6K+ real websites |
| Dribbble | 284 | Popular web & product design shots from professional designers |
| Awwwards | 300 | Site of the Day winners — award-winning web design |
| Curated | 90 | Hand-picked patterns from top SaaS products (Stripe, Linear, Notion, etc.) |
| Landbook | 90 | Landing page gallery screenshots |

**Total: 7,080 patterns**, all quality-scored 0-10.

## Quality Scoring

Every pattern is scored based on:
- **Source quality** — curated > Awwwards > Dribbble > dataset
- **Metadata completeness** — specific page types, industry tags, layout info
- **Design signals** — UX patterns, component hints, accessibility notes
- **Tag richness** — freeform tags for better search

Search results are ranked by quality score, so the best examples surface first.

## Screenshots

The repo includes **560+ high-resolution design screenshots** across all sources:
- Dribbble: 284 shots (1600px wide, web design + product design)
- Awwwards: 300 shots (1600x1200, SOTD winners)
- Curated: 68 shots (top SaaS products)
- Landbook: 90 shots (landing pages)

## Running Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

38 tests covering schema validation, database operations, all 6 MCP tools, data quality checks, and end-to-end integration workflows.

## Project Structure

```
design-mcp/
├── server.py              # FastMCP server — 6 tool definitions
├── schema.py              # Pydantic models (DesignPattern, Platform, LayoutType)
├── database.py            # JSON database with search/filter
├── enrichment.py          # LLM-based metadata enrichment (optional)
├── data/
│   ├── patterns.json      # 7,080 design patterns (quality-sorted)
│   ├── taxonomy.json      # Tag taxonomy
│   └── tokens/
│       └── semantic_tokens.json  # W3C-format semantic tokens
├── screenshots/           # 560+ high-res design screenshots
│   ├── dribbble/          # 284 popular shots
│   ├── awwwards/          # 300 SOTD winners
│   ├── curated/           # 68 top SaaS products
│   └── landbook/          # 90 landing pages
├── prompts/               # Prompt templates for AI agents
├── scripts/               # Data ingestion & scraping scripts
└── tests/
    └── test_design_mcp.py # 38 comprehensive tests
```

## Using on Another Machine

Just clone the repo — all patterns and screenshots are included. No external API keys or dataset downloads needed.

```bash
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python -m venv .venv && .venv/Scripts/Activate.ps1
pip install fastmcp pydantic httpx uvicorn
# Add to Claude Desktop or Cursor config, done!
```

## Tech Stack

- **FastMCP** — MCP server framework
- **Pydantic** — Schema validation
- **httpx** — Async HTTP client
- **Python 3.12+**

## License

MIT
