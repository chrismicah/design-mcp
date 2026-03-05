# Design Intelligence MCP Server

An MCP (Model Context Protocol) server that gives AI agents structured access to **6,300+ real-world design patterns** — enabling higher-quality UI generation by studying how established products handle design challenges.

## Why This Exists

When AI agents generate UIs, they often produce generic layouts with magic numbers, poor component structure, and no understanding of UX patterns. This MCP server fixes that by providing:

- **Structured metadata** about real-world designs (layout types, component hints, behavioral descriptions)
- **Quality-ranked results** so agents reference the best examples first
- **Semantic tokens** for consistent styling instead of hardcoded values
- **Behavioral patterns** describing how UX patterns should *work*, not just *look*

Research shows that **structured metadata matters more than screenshots** for LLM-driven UI generation.

## Quick Start

### 1. Install Dependencies

```bash
cd design-mcp
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install fastmcp pydantic httpx uvicorn huggingface-hub
```

### 2. Configure Your MCP Host

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "design-intelligence": {
      "command": "python",
      "args": ["path/to/design-mcp/server.py"]
    }
  }
}
```

**Cursor** (Settings → MCP Servers → Add):
```
Name: Design Intelligence
Command: python path/to/design-mcp/server.py
```

### 3. Use It

Once configured, your AI agent has 6 new tools:

```
"Search for fintech dashboard patterns with dark mode"
→ Returns quality-ranked design blueprints with layout info, component hints, etc.

"Compare how different products handle pricing pages"
→ Side-by-side comparison of layout strategies and component choices
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_design_patterns` | Search 6,300+ patterns by query, page type, industry, style, etc. |
| `get_design_blueprint` | Get full design blueprint for a specific pattern |
| `get_semantic_tokens` | Get W3C-format design tokens for consistent styling |
| `get_design_taxonomy` | Browse available categories, page types, UI elements |
| `get_behavioral_pattern` | Get behavioral specs (empty states, loading, error handling, etc.) |
| `compare_design_approaches` | Compare how different products solve the same design problem |

## Data Sources

| Source | Count | Quality | Description |
|--------|-------|---------|-------------|
| Curated | 22 | ⭐⭐⭐ | Hand-picked from Stripe, Linear, Notion, Vercel |
| Awwwards | 30+ | ⭐⭐⭐ | Award-winning Sites of the Day |
| Dribbble | 151 | ⭐⭐ | Popular shots from top designers |
| webui-7kbal | 6,134 | ⭐ | HuggingFace academic dataset with HTML/CSS/accessibility trees |

### Expanding the Dataset

To add the full webui-7kbal raw data (for re-processing or enrichment):

```bash
pip install huggingface-hub
python scripts/ingest_webui7k.py
```

This downloads ~7K web UI samples from HuggingFace and processes them into design patterns.

## Quality Scoring

Every pattern has a `quality_score` (0-10) based on:
- **Metadata completeness** — layout type, color mode, behavioral description, etc.
- **UI element richness** — diversity of components
- **Source quality** — curated > awwwards > dribbble > webui-7kbal
- **Accessibility info** — presence of ARIA/WCAG notes

Search results are ranked by quality score, so agents always see the best examples first.

## Project Structure

```
design-mcp/
├── server.py              # FastMCP server — 6 tool definitions
├── schema.py              # Pydantic models (DesignPattern)
├── database.py            # JSON database with search
├── models/
│   ├── quality_scorer.py  # Heuristic quality scoring
│   └── train_scorer.py    # Score all patterns
├── data/
│   ├── patterns.json      # Main database (6,300+ patterns)
│   ├── taxonomy.json      # Available categories
│   └── tokens/            # Semantic design tokens
├── tests/                 # 66 pytest tests
├── scripts/               # Data ingestion scripts
├── prompts/               # MCP prompt templates
└── screenshots/           # Design screenshots
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Using on Another Machine

1. Clone this repo
2. Create a venv and install deps: `pip install fastmcp pydantic httpx uvicorn`
3. Configure your MCP host (see Quick Start above)
4. Done — `patterns.json` is included in the repo with all 6,300+ patterns

The raw webui-7kbal dataset is **not** included (too large). Only the processed patterns are in the repo.

## License

MIT
