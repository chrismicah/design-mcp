# Design Intelligence MCP Server — Full Implementation Plan

> **For: Coding Agent (Claude Code / Cursor)**
> **Goal:** Build a fully functional MCP server that gives AI agents structured access to real-world design patterns, enabling higher-quality UI generation.
> **Browser Automation:** Playwriter MCP (NOT Playwright)
> **Server Framework:** FastMCP (Python)
> **Timeline:** 1–2 days

---

## Table of Contents

1. [Accounts & Prerequisites](#1-accounts--prerequisites)
2. [Project Structure](#2-project-structure)
3. [Phase 1: Schema Design](#3-phase-1-schema-design)
4. [Phase 2: Data Harvesting with Playwriter MCP](#4-phase-2-data-harvesting-with-playwriter-mcp)
5. [Phase 3: FastMCP Server Implementation](#5-phase-3-fastmcp-server-implementation)
6. [Phase 4: Blueprint & Prompt Templates](#6-phase-4-blueprint--prompt-templates)
7. [Phase 5: Token Optimization](#7-phase-5-token-optimization)
8. [Phase 6: Integration & Testing](#8-phase-6-integration--testing)
9. [Appendix: Research-Backed Schema Decisions](#9-appendix-research-backed-schema-decisions)

---

## 1. Accounts & Prerequisites

### Required (Free)
- **GitHub** — for project repo
- **Dribbble** — free account, public search access
- **Awwwards** — no account needed for public browsing
- **Figma** — free account for accessing community design files and token specs

### Optional
- **Refero Pro** — only if you want their specific curated flows. You can replicate their taxonomy without it.

### Required (Free — Primary Dataset)
- **HuggingFace account** — free, needed to download the `biglab/webui-7kbal` dataset. This is your **best and first data source** because it includes structured view hierarchy JSON alongside screenshots, not just images. 7,000 curated, balanced web UIs with HTML/CSS and element data.

### Tools (All Free/Open Source)
- **Python 3.11+**
- **FastMCP** — `pip install fastmcp`
- **Pydantic** — `pip install pydantic` (comes with FastMCP)
- **httpx** — `pip install httpx` (async HTTP client)
- **Playwriter MCP** — installed and configured in your host environment
- **Claude Desktop or Cursor** — as the MCP host

### Install Commands
```bash
mkdir design-mcp && cd design-mcp
python -m venv .venv && source .venv/bin/activate
pip install fastmcp pydantic httpx uvicorn huggingface-hub
```

---

## 2. Project Structure

```
design-mcp/
├── server.py                    # Main FastMCP server — all tool definitions
├── schema.py                    # Pydantic models for design patterns
├── database.py                  # JSON database read/write helpers
├── enrichment.py                # LLM-based metadata enrichment (optional)
├── prompts/
│   ├── analyze_screen.md        # Prompt template: analyze a design screenshot
│   ├── generate_blueprint.md    # Prompt template: create a UI blueprint
│   └── compare_patterns.md      # Prompt template: compare design approaches
├── data/
│   ├── patterns.json            # Main design pattern database
│   ├── taxonomy.json            # Tag taxonomy (page types, UX patterns, UI elements)
│   └── tokens/
│       ├── semantic_tokens.json # Tier 2 semantic design tokens
│       └── component_tokens.json# Tier 3 component-specific tokens
├── scraping/
│   ├── dribbble_plan.md         # Instructions for Playwriter MCP scraping
│   └── awwwards_plan.md         # Instructions for Playwriter MCP scraping
└── claude_desktop_config.json   # Example host configuration
```

---

## 3. Phase 1: Schema Design

This is the most important phase. The research is clear: **structured metadata matters more than screenshots** for LLM-driven UI generation. Every field in this schema exists because research shows it improves output quality.

### 3.1 Core Design Pattern Schema (`schema.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Platform(str, Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"

class LayoutType(str, Enum):
    """Research finding: Explicit layout type prevents brittle absolute positioning."""
    FLEXBOX = "flexbox"
    CSS_GRID = "css_grid"
    BENTO_GRID = "bento_grid"
    SINGLE_COLUMN = "single_column"
    SIDEBAR_MAIN = "sidebar_main"
    SPLIT_SCREEN = "split_screen"
    MASONRY = "masonry"
    STACKED = "stacked"

class DesignPattern(BaseModel):
    """
    A single design pattern/screen in the database.
    Schema fields are chosen based on empirical research into what
    metadata most improves LLM UI generation quality.
    """

    # === IDENTITY ===
    id: str = Field(description="Unique identifier")
    name: str = Field(description="Descriptive name, e.g. 'Stripe Dashboard Empty State'")
    source: str = Field(description="Origin platform: dribbble, awwwards, webui-7kbal, etc.")
    source_url: str = Field(description="Original URL for reference")
    image_url: Optional[str] = Field(default=None, description="Screenshot URL if available")

    # === TAXONOMY (High impact — acts as semantic anchor for the LLM) ===
    page_type: str = Field(description="E.g. 'Dashboard', 'Pricing Table', '404 Page', 'Onboarding', 'Settings'")
    ux_patterns: list[str] = Field(
        default_factory=list,
        description="E.g. ['Skeleton Loading', 'Progressive Disclosure', 'Multi-Step Form', 'Empty State']"
    )
    ui_elements: list[str] = Field(
        default_factory=list,
        description="E.g. ['Accordion', 'Avatar', 'Badge', 'Toggle', 'Date Picker', 'Modal']"
    )
    industry: Optional[str] = Field(default=None, description="E.g. 'Fintech', 'Health', 'E-Commerce', 'SaaS', 'Education'")

    # === LAYOUT (High impact — prevents absolute positioning hallucination) ===
    layout_type: Optional[LayoutType] = Field(
        default=None,
        description="Primary layout strategy. Research shows this alone significantly improves structural output."
    )
    layout_notes: Optional[str] = Field(
        default=None,
        description="Brief description: 'Sidebar 280px fixed, main content scrollable with 24px gap grid'"
    )

    # === VISUAL STYLE (Medium impact — useful for global styling) ===
    platform: Platform = Field(default=Platform.WEB)
    color_mode: Optional[str] = Field(default=None, description="'light', 'dark', or 'auto'")
    visual_style: list[str] = Field(
        default_factory=list,
        description="E.g. ['Glassmorphism', 'Minimal', 'Brutalist', 'Neubrutalism', 'Flat', 'Skeuomorphic']"
    )
    primary_colors: list[str] = Field(
        default_factory=list,
        description="Dominant hex colors observed: ['#1a1a2e', '#e94560', '#0f3460']"
    )

    # === BEHAVIORAL CONTEXT (High impact — gives the LLM interaction logic) ===
    behavioral_description: Optional[str] = Field(
        default=None,
        description=(
            "How this pattern BEHAVES, not just looks. E.g.: "
            "'Empty state educates user on feature value, shows illustration, "
            "provides single prominent CTA to create first item. "
            "Loading shows skeleton matching final layout. "
            "Error state offers retry with preserved form data.'"
        )
    )

    # === COMPONENT PROPS (High impact — prevents hallucinated component structure) ===
    component_hints: list[dict] = Field(
        default_factory=list,
        description=(
            "Known component structures. E.g.: "
            "[{'name': 'PricingCard', 'props': ['tier', 'price', 'features', 'cta_text', 'is_popular']}]"
        )
    )

    # === ACCESSIBILITY (High impact — 60% reduction in inaccessibility when provided) ===
    accessibility_notes: Optional[str] = Field(
        default=None,
        description=(
            "E.g. 'Requires ARIA landmarks for nav, main, complementary. "
            "Color contrast must meet WCAG AA (4.5:1 for text). "
            "All interactive elements need visible focus indicators.'"
        )
    )

    # === SEMANTIC TOKENS (High impact — avoids magic numbers) ===
    semantic_tokens: Optional[dict] = Field(
        default=None,
        description=(
            "Tier 2 semantic tokens observed or inferred. E.g.: "
            "{'color-background-primary': '#1a1a2e', 'spacing-section': '48px', "
            "'border-radius-card': '12px', 'font-heading': 'Inter'}"
        )
    )

    # === META ===
    quality_score: Optional[float] = Field(
        default=None, ge=0, le=10,
        description="Subjective quality rating. Used for search ranking."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Freeform tags for search: ['saas', 'dark-mode', 'illustration', 'startup']"
    )
```

### 3.2 Taxonomy File (`data/taxonomy.json`)

```json
{
    "page_types": [
        "Landing Page", "Pricing", "Dashboard", "Settings", "Profile",
        "Onboarding", "Login", "Signup", "404 Page", "Checkout",
        "Product Page", "Search Results", "Blog Post", "Documentation",
        "File Explorer", "Chat Interface", "Calendar", "Kanban Board",
        "Analytics", "Invoice", "Email Template", "Notifications",
        "Admin Panel", "Marketplace", "Social Feed"
    ],
    "ux_patterns": [
        "Empty State", "Skeleton Loading", "Progressive Disclosure",
        "Multi-Step Form", "Guided Tour", "Onboarding Flow",
        "Infinite Scroll", "Pull to Refresh", "Swipe Actions",
        "Drag and Drop", "Inline Editing", "Bulk Actions",
        "Command Palette", "Contextual Menu", "Toast Notifications",
        "Undo/Redo", "Optimistic Update", "Lazy Loading",
        "Virtualized List", "Breadcrumb Navigation", "Tab Navigation",
        "Stepper", "Accordion Navigation", "Search with Filters",
        "Password Reset Flow", "Account Deletion Flow"
    ],
    "ui_elements": [
        "Accordion", "Avatar", "Badge", "Breadcrumb", "Button",
        "Card", "Carousel", "Checkbox", "Chip", "Code Snippet",
        "Collapsible", "Color Picker", "Combobox", "Data Table",
        "Date Picker", "Dialog", "Divider", "Drawer", "Dropdown",
        "File Upload", "Icon", "Input", "Mini Player", "Modal",
        "Navigation Bar", "Pagination", "Popover", "Progress Bar",
        "Radio Button", "Range Slider", "Rich Text Editor",
        "Segmented Control", "Select", "Sidebar", "Skeleton",
        "Slider", "Spinner", "Stepper", "Switch", "Tabs",
        "Tag", "Text Area", "Timeline", "Toast", "Toggle",
        "Tooltip", "Tree View"
    ],
    "industries": [
        "Fintech", "Health & Wellness", "E-Commerce", "SaaS",
        "Education", "Social Media", "Productivity", "Travel",
        "Real Estate", "Food & Delivery", "Entertainment",
        "Developer Tools", "HR & Recruiting", "CRM", "IoT"
    ],
    "visual_styles": [
        "Minimal", "Brutalist", "Neubrutalism", "Glassmorphism",
        "Flat", "Material", "Skeuomorphic", "Gradient-Heavy",
        "Monochrome", "Retro", "Futuristic", "Organic",
        "Editorial", "Luxury", "Playful", "Corporate"
    ]
}
```

### 3.3 Semantic Tokens Template (`data/tokens/semantic_tokens.json`)

```json
{
    "$schema": "https://design-tokens.github.io/community-group/format/",
    "description": "Tier 2 Semantic Tokens — provide these to the LLM for consistent styling",
    "color": {
        "background": {
            "primary": { "$value": "{primitive.neutral.50}", "$type": "color" },
            "secondary": { "$value": "{primitive.neutral.100}", "$type": "color" },
            "inverse": { "$value": "{primitive.neutral.900}", "$type": "color" },
            "brand": { "$value": "{primitive.blue.500}", "$type": "color" },
            "danger": { "$value": "{primitive.red.500}", "$type": "color" },
            "success": { "$value": "{primitive.green.500}", "$type": "color" }
        },
        "text": {
            "primary": { "$value": "{primitive.neutral.900}", "$type": "color" },
            "secondary": { "$value": "{primitive.neutral.600}", "$type": "color" },
            "on-brand": { "$value": "{primitive.white}", "$type": "color" }
        },
        "border": {
            "default": { "$value": "{primitive.neutral.200}", "$type": "color" },
            "focus": { "$value": "{primitive.blue.400}", "$type": "color" }
        }
    },
    "spacing": {
        "xs": { "$value": "4px", "$type": "dimension" },
        "sm": { "$value": "8px", "$type": "dimension" },
        "md": { "$value": "16px", "$type": "dimension" },
        "lg": { "$value": "24px", "$type": "dimension" },
        "xl": { "$value": "32px", "$type": "dimension" },
        "2xl": { "$value": "48px", "$type": "dimension" },
        "section": { "$value": "64px", "$type": "dimension" }
    },
    "borderRadius": {
        "sm": { "$value": "4px", "$type": "dimension" },
        "md": { "$value": "8px", "$type": "dimension" },
        "lg": { "$value": "12px", "$type": "dimension" },
        "full": { "$value": "9999px", "$type": "dimension" }
    },
    "typography": {
        "heading": {
            "fontFamily": { "$value": "Inter", "$type": "fontFamily" },
            "fontWeight": { "$value": "700", "$type": "fontWeight" }
        },
        "body": {
            "fontFamily": { "$value": "Inter", "$type": "fontFamily" },
            "fontWeight": { "$value": "400", "$type": "fontWeight" }
        }
    }
}
```

---

## 4. Phase 2: Data Ingestion & Harvesting

### IMPORTANT: Data Source Priority

There are TWO data pipelines. Do them in order:

1. **Phase 2A: `webui-7kbal` dataset (do this FIRST)** — Structured, local, no scraping needed. This gives you ~7,000 patterns with actual HTML/CSS and view hierarchy data. This is your foundation.
2. **Phase 2B: Playwriter MCP scraping (do this SECOND)** — Supplements the dataset with fresher, curated examples from Dribbble and Awwwards. Adds visual diversity and industry-specific context that the academic dataset lacks.

---

### Phase 2A: Ingest `biglab/webui-7kbal` from HuggingFace

This is the highest-value, lowest-effort data source. No scraping, no rate limits, no CAPTCHAs.

#### Step 1: Download the Dataset (Metadata Only — Skip Screenshots)

```python
from huggingface_hub import snapshot_download

dataset_path = snapshot_download(
    repo_id="biglab/webui-7kbal",
    repo_type="dataset",
    allow_patterns=["*.json", "*.html", "*.htm"],
    ignore_patterns=["*.png", "*.jpg", "*.jpeg"]
)
print(f"Downloaded to: {dataset_path}")
```

#### Step 2: Explore the Structure

The coding agent should:
1. Download the dataset
2. List the directory structure to understand the format
3. Open 3-5 sample entries to understand the JSON schema
4. Then build the ingestion script

#### Step 3: Build the Ingestion Script

The coding agent should explore the actual dataset structure first, then build an ingestion script that maps the data to the DesignPattern schema. Key priorities:
- Use view hierarchy JSON for layout/element extraction
- Parse HTML for CSS classes, element types, ARIA attributes
- Infer page types from URLs and content
- Quality filter to remove broken/low-quality entries

---

### Phase 2B: Supplemental Scraping with Playwriter MCP

Create scraping plans for Dribbble and Awwwards (see scraping/ directory). User will handle logins and CAPTCHAs. Target ~500 from Dribbble, ~300 from Awwwards.

---

## 5. Phase 3: FastMCP Server Implementation

Implement 6 tools:
1. `search_design_patterns` — primary discovery
2. `get_design_blueprint` — detailed pattern view
3. `get_semantic_tokens` — design token system
4. `get_design_taxonomy` — available categories
5. `get_behavioral_pattern` — UX behavior specs
6. `compare_design_approaches` — side-by-side comparison

See the full implementation code in the design doc for server.py, database.py, and enrichment.py.

---

## 6. Phase 4: Blueprint & Prompt Templates

Create MCP Prompt primitives in prompts/ directory for:
- Screen analysis
- UI generation blueprints
- Pattern comparison

---

## 7. Phase 5: Token Optimization

- Selective loading (condensed blueprints by default)
- Field filtering parameter
- Total design context budget: ~5,400 tokens (<3% of 200k window)

---

## 8. Phase 6: Integration & Testing

Configure for Claude Desktop/Cursor and run 5 test prompts to verify all tools work correctly.

---

## Environment Notes

- HuggingFace API Token: Available as HF_TOKEN environment variable
- Python: 3.12.9
- OS: Windows 10/11
