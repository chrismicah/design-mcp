# Design Intelligence MCP Server

An MCP (Model Context Protocol) server that gives AI agents structured access to **7,000+ real-world design patterns** for higher-quality UI generation — including visual design analysis, anti-pattern detection, and actionable improvement suggestions.

Instead of hallucinating layouts and guessing at component structures, AI agents can search proven design patterns, get semantic tokens, analyze code for visual quality, and generate complete design systems before writing code.

## Why This Exists

Research shows that LLMs generate significantly better UI code when given:
- **Explicit layout types** (prevents absolute positioning hallucination)
- **Behavioral descriptions** (how patterns work, not just how they look)
- **Semantic tokens** (avoids magic numbers and hardcoded colors)
- **Component structure hints** (prevents hallucinated prop interfaces)
- **Accessibility notes** (60% reduction in inaccessibility issues)
- **Visual design rules** (color contrast, typography scales, spacing systems)

This MCP server provides all of that from a curated database of real-world examples.

---

## Installation

### Prerequisites

- **Python 3.12+**
- **Git**

### Step 1: Clone & Install Dependencies

**macOS / Linux:**
```bash
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp pydantic httpx uvicorn
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastmcp pydantic httpx uvicorn
```

### Step 2: Verify Installation

```bash
python -m pytest tests/ -q
# Expected: 212 passed
```

---

## Connecting to AI Tools

### Claude Code CLI (Recommended)

The fastest way to add the MCP to Claude Code:

**macOS / Linux:**
```bash
claude mcp add design-intelligence -- \
  /path/to/design-mcp/.venv/bin/python \
  /path/to/design-mcp/server.py
```

**Windows (PowerShell):**
```powershell
claude mcp add-json design-intelligence '{\"command\":\"C:\\path\\to\\design-mcp\\.venv\\Scripts\\python.exe\",\"args\":[\"C:\\path\\to\\design-mcp\\server.py\"]}'
```

To verify it's registered:
```bash
claude mcp list
```

To remove:
```bash
claude mcp remove design-intelligence
```

### Claude Desktop

Add to your config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "design-intelligence": {
      "command": "/path/to/design-mcp/.venv/bin/python",
      "args": ["/path/to/design-mcp/server.py"]
    }
  }
}
```

> **Windows paths:** Use double backslashes in JSON:  
> `"command": "C:\\Users\\you\\Projects\\design-mcp\\.venv\\Scripts\\python.exe"`

### Cursor

Settings → MCP Servers → Add:
- **Name:** `design-intelligence`
- **Command:** `/path/to/design-mcp/.venv/bin/python /path/to/design-mcp/server.py`

### Windsurf / Other MCP Clients

Any MCP-compatible client can connect. The server uses **stdio** transport (FastMCP default). Point your client to:

```
command: /path/to/.venv/bin/python
args: ["/path/to/server.py"]
```

---

## Usage

Once connected, ask your AI agent things like:

- *"Search for dark mode dashboard designs in fintech"*
- *"Get the full blueprint for Stripe's dashboard pattern"*
- *"Analyze this code for design anti-patterns"*
- *"Scan my project and tell me what to fix"*
- *"Give me visual suggestions — colors, fonts, spacing — for a professional law firm app"*
- *"Compare how Stripe vs Linear vs Notion handle their dashboards"*
- *"What libraries should I use for a glassmorphism landing page with animations?"*

---

## MCP Tools (12)

### Search & Discovery

#### `search_design_patterns`
Search 7,000+ design patterns with filters for page type, industry, platform, color mode, and visual style.

```python
results = search_design_patterns(
    query="analytics dashboard",
    page_type="Dashboard",
    industry="Fintech",
    color_mode="dark",
    limit=5
)
```

#### `get_design_blueprint`
Get the full blueprint for a specific pattern — layout info, component hints with code, behavioral descriptions, accessibility notes, and semantic tokens.

#### `get_design_taxonomy`
Browse the full taxonomy: 25 page types, 25 UX patterns, 47 UI elements, 15 industries, 16 visual styles.

#### `compare_design_approaches`
Compare how different products handle the same page type — side-by-side blueprints with layout strategies and key differences.

### Design Tokens & Behavior

#### `get_semantic_tokens`
Get W3C-format semantic design tokens for consistent styling — colors, spacing, typography, borders. Supports light and dark themes.

#### `get_behavioral_pattern`
Get behavioral specs for 7 common UX patterns: empty states, skeleton loading, error handling, onboarding flows, form validation, infinite scroll, command palettes.

### Code Analysis

#### `analyze_and_devibecode`
**Anti-pattern detector.** Paste raw "vibecoded" code and get a structured refactoring plan with 15 anti-pattern detectors across styling, layout, and accessibility.

```python
result = analyze_and_devibecode("""
    <div onClick={fn} className="bg-[#FF0000] w-[300px] absolute top-[20px]">
        <input type="text" />
    </div>
""")
# Returns: anti_patterns_found, severity_summary, refactoring_suggestions,
#          recommended_layout, semantic_tokens, component_hints
```

#### `scan_project`
**Project-wide scanner.** Point at a directory and get a health score (0-100), per-file reports, visual analysis, priority fixes, and library recommendations.

```python
result = scan_project(
    project_path="/path/to/my-app/src",
    max_files=50
)
# Returns: project_health_score, files_scanned, top_issues,
#          visual_issues, recommended_libraries, file_reports
```

Detects 21 issue types across structural, visual, and accessibility domains:
- **Structural:** div soup, missing flex/grid, redundant wrappers, absolute positioning abuse
- **Styling:** magic hex colors, hardcoded pixels, inline styles, z-index abuse
- **Accessibility:** missing ARIA, unlabeled inputs, removed focus indicators, interactive divs
- **Visual:** low contrast (WCAG), color proliferation, spacing inconsistency, typography scale issues, broken heading hierarchy, missing dark mode

#### `generate_refactored_code`
Takes vibecoded code and generates a concrete refactoring plan mapped to a specific component library (shadcn/ui, Mantine, Chakra UI, NextUI, or Radix UI).

### Visual Design

#### `get_visual_suggestions`
**Visual design system generator.** Analyzes code for color, typography, and spacing quality, then generates a complete design system with actionable CSS/Tailwind values.

```python
result = get_visual_suggestions(
    source_code=my_code,
    primary_color="#3b82f6",     # Optional — auto-detects from code
    brand_style="professional",  # clean_modern|editorial|geometric|friendly|professional|brutalist
    spacing_density="comfortable" # compact|comfortable|spacious
)
# Returns: visual_analysis, color_palette (with shades 50-950),
#          typography (font pairing + type scale), spacing system,
#          CSS variables, Tailwind config, Google Fonts URL, quick_wins
```

**Includes:**
- Color palette generator (11 shades, light/dark themes, CSS variables, complementary/analogous)
- 6 curated font pairings by brand personality
- Type scales (major third, perfect fourth)
- 3 spacing density systems (compact, comfortable, spacious)
- Quick wins prioritizer (top 5 highest-impact visual fixes)

### Libraries

#### `get_library_recommendations`
Get recommended frontend libraries based on your project needs — maps use cases, UI elements, and visual styles to the best React libraries.

```python
result = get_library_recommendations(
    use_case="dashboard",
    ui_elements=["Data Table", "Modal", "Button"],
    needs_charts=True
)
# Returns: shadcn/ui, Recharts, Tailwind — with install commands + code examples
```

#### `get_library_details`
Get full details for any of 18 supported libraries — components list, install command, code examples, and what it pairs with.

**Supported libraries:** shadcn/ui, Radix UI, Mantine, Chakra UI, NextUI, React Bits, Tailwind CSS, Panda CSS, Vanilla Extract, Framer Motion, GSAP, React Spring, Three.js/R3F, Lottie, tsParticles, D3.js, Recharts, Victory.

---

## Data Sources

| Source | Patterns | Description |
|--------|----------|-------------|
| webui-7kbal | 6,134 | HuggingFace dataset — real websites with accessibility trees |
| Dribbble | 284 | Popular web & product design shots from professional designers |
| Awwwards | 300 | Site of the Day winners — award-winning web design |
| Curated | 90 | Hand-picked patterns from top SaaS products (Stripe, Linear, Notion, etc.) |
| Landbook | 90 | Landing page gallery screenshots |

**Total: 7,080 patterns**, all quality-scored 0-10, with 742 vision-analyzed screenshots.

### Data Completeness

| Field | Coverage |
|-------|----------|
| Semantic tokens | 100% (7,080/7,080) |
| Behavioral descriptions | 97% (6,882/7,080) |
| Accessibility notes | 97% (6,882/7,080) |
| Component hints | 47% (3,356/7,080) |
| Vision analysis (colors, layout) | 742 screenshots |

---

## Running Tests

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

**212 tests** covering:
- Schema validation (16 tests)
- Database operations (25 tests)
- Anti-pattern analyzer (49 tests)
- Visual analyzer — colors, spacing, typography, palette generation (36 tests)
- Server tools (28 tests)
- Library recommendations (30 tests)
- Integration workflows (28 tests)

---

## Project Structure

```
design-mcp/
├── server.py                    # FastMCP server — 12 MCP tools
├── schema.py                    # Pydantic models (DesignPattern, Platform, LayoutType)
├── database.py                  # JSON database with search/filter/ranking
├── models/
│   ├── analyzer.py              # Structural anti-pattern detector (15 detectors)
│   └── visual_analyzer.py       # Visual design analyzer (colors, typography, spacing)
├── data/
│   ├── patterns.json            # 7,080 design patterns (11.7 MB, optimized)
│   ├── vision_results.json      # 742 screenshot analysis results
│   ├── libraries.json           # 18 libraries with mapping rules
│   ├── taxonomy.json            # Tag taxonomy
│   ├── tokens/
│   │   └── semantic_tokens.json # Light/dark semantic token sets
│   ├── layout_templates.json    # Layout code templates
│   ├── behavioral_templates.json # 14 behavioral pattern templates
│   └── component_code.json      # 17 component code templates (shadcn/ui TSX)
├── screenshots/                 # 742 high-res design screenshots
│   ├── dribbble/                # 284 popular shots
│   ├── awwwards/                # 300 SOTD winners
│   ├── curated/                 # 68 top SaaS products
│   └── landbook/                # 90 landing pages
├── scripts/                     # Data ingestion, scraping, enrichment scripts
└── tests/
    ├── test_analyzer.py         # Anti-pattern detector tests
    ├── test_visual_analyzer.py  # Visual analyzer tests
    ├── test_database.py         # Database tests
    ├── test_schema.py           # Schema validation tests
    ├── test_server.py           # Server tool tests
    ├── test_libraries.py        # Library recommendation tests
    └── test_design_mcp.py       # Integration tests
```

---

## Using on Another Machine

Just clone the repo — all patterns, screenshots, and reference data are included. No external API keys or dataset downloads needed.

**macOS:**
```bash
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install fastmcp pydantic httpx uvicorn

# Add to Claude Code
claude mcp add design-intelligence -- \
  "$(pwd)/.venv/bin/python" \
  "$(pwd)/server.py"
```

**Windows:**
```powershell
git clone https://github.com/chrismicah/design-mcp.git
cd design-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastmcp pydantic httpx uvicorn

# Add to Claude Code
claude mcp add-json design-intelligence ('{{"command":"{0}\\.venv\\Scripts\\python.exe","args":["{0}\\server.py"]}}' -f (Get-Location).Path)
```

---

## Tech Stack

- **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server framework
- **[Pydantic](https://docs.pydantic.dev/)** — Schema validation
- **Python 3.12+** — No external AI/ML dependencies required

## License

MIT
