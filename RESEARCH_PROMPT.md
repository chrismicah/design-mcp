# Research Prompt: Fixing the Design Intelligence MCP

## Context

We built a Design Intelligence MCP Server (https://github.com/chrismicah/design-mcp) that's supposed to give AI agents structured access to real-world design patterns for higher-quality UI generation. It has 12 MCP tools, 7,080 patterns, 742 vision-analyzed screenshots, and 212 passing tests.

**The problem: it's mostly hollow.** The infrastructure works, but the data quality is poor. An AI using this MCP still vibecodes because the pattern data doesn't contain actionable design intelligence.

## Architecture

```
Screenshots (742) → Vision Analysis → vision_results.json
                                          ↓ (NOT CONNECTED)
HuggingFace dataset (6,134) → patterns.json (7,080 entries)
Dribbble/Awwwards/Curated   ↗     ↑
                              enrichment scripts add
                              templates based on page_type
```

### Current Data Quality (honest)

| Field | "Coverage" | Reality |
|-------|-----------|---------|
| semantic_tokens | 100% | 99.9% are just the string "light" or "dark" — references to ONE generic token set, not real per-pattern tokens |
| behavioral_description | 97% | All same-type patterns get identical template text. Every landing page has the same description. |
| accessibility_notes | 97% | Same template issue — all dashboards get identical a11y notes |
| primary_colors | 0.3% | Only 22 hand-crafted patterns have colors. Vision results (742 screenshots) were analyzed but NEVER merged back. |
| component_hints | 47% | Hints like `[component:Card]` are placeholders for generic shadcn/ui code, not adapted to the pattern |
| layout_notes | 91% | These are actually decent — from the original HuggingFace dataset |

### What Works
- The 22 curated seed patterns (Stripe, Linear, Notion, Vercel, etc.) are high-quality with real colors, tokens, behavior
- The code analyzer (21 anti-pattern detectors) genuinely catches issues
- The visual analyzer (color contrast, typography scale, spacing) is real and useful
- The library recommendation engine maps use cases to libraries correctly
- scan_project produces honest health scores

### What Doesn't Work
1. **Search returns empty patterns** — when an AI searches for "dark dashboard fintech," it gets patterns with no colors, no real tokens, no specific behavioral descriptions
2. **Vision data is orphaned** — 742 screenshots analyzed, results sit in vision_results.json, never merged into patterns.json
3. **Templates instead of intelligence** — the enrichment scripts stamp the same text onto every pattern of the same type instead of extracting unique insights
4. **The MCP doesn't improve AI output** — I (an AI agent with full access to all 12 tools) built a demo site and it came out vibecoded. The tools returned data, but nothing actionable enough to change my behavior.

## The Files

```
server.py                         # 12 MCP tools (FastMCP)
schema.py                         # Pydantic models  
database.py                       # JSON search/filter
models/analyzer.py                # 15 structural anti-pattern detectors
models/visual_analyzer.py         # 6 visual design detectors + palette generator
data/patterns.json                # 7,080 patterns (11.7MB) — mostly hollow
data/vision_results.json          # 742 screenshot analyses — ORPHANED, not merged
data/libraries.json               # 18 libraries with mapping rules
data/tokens/semantic_tokens.json  # ONE light + ONE dark token set (generic)
data/behavioral_templates.json    # 14 behavioral templates (assigned by page_type)
data/component_code.json          # 17 component code templates (generic shadcn/ui)
data/layout_templates.json        # Layout code templates
scripts/build_real_data.py        # Enrichment script (stamps templates)
scripts/optimize_data.py          # Compresses patterns.json
```

## Research Questions

### 1. How should vision data be merged into patterns?
We have 742 vision results with: page_type, ui_elements, visual_style, primary_colors, layout_type, quality_score. These need to flow back into patterns.json for the ~6,134 HuggingFace patterns that have matching screenshots. What's the right merge strategy? Match by filename/URL? What about the ~6,000 patterns without screenshots?

### 2. How do we generate REAL per-pattern semantic tokens?
Currently every pattern gets "light" or "dark." A real system would:
- Extract the actual color palette from the vision analysis (primary_colors)
- Generate a full shade scale (50-950) from each primary color
- Create light/dark theme token sets specific to THAT pattern's palette
- Include spacing and typography tokens derived from the actual design

What's the best approach? Generate tokens from vision colors? Use the visual_analyzer's palette generator at enrichment time?

### 3. How do we make behavioral descriptions unique per pattern?
Currently all landing pages get the same text. Options:
- Use the pattern's specific UI elements + layout to generate tailored descriptions
- Cluster patterns by visual_style + ui_elements and write descriptions per cluster
- Use an LLM to generate unique descriptions (expensive for 7,080 patterns)
- Accept that template-based is OK but make MORE granular templates (not just by page_type, but by page_type + layout_type + visual_style)

### 4. How should the MCP actually change AI coding behavior?
The fundamental question: when an AI calls `search_design_patterns("dark dashboard")`, what data would actually cause it to write better code than it would without the MCP? 

Ideas to research:
- **Concrete CSS/Tailwind snippets** instead of abstract descriptions
- **Before/after code examples** showing the transformation from vibecoded to designed
- **Decision trees** — "If building a dashboard, use sidebar_main layout with these specific spacing values"
- **Anti-pattern → fix mapping** — when scan_project finds an issue, return the exact code fix, not just a description

### 5. What does the competition do?
Research these tools and see what they get right:
- **v0 by Vercel** — how does it generate good UI consistently?
- **Magic Patterns** — what data/approach do they use?
- **Galileo AI** — how do they handle design-to-code?
- **Figma's AI features** — what design intelligence do they encode?
- **Locofy, Anima** — design-to-code tools, what patterns do they use?

### 6. Should we reduce pattern count and increase quality?
Maybe 7,080 low-quality patterns is worse than 200 high-quality ones. Research:
- What's the minimum viable pattern count for good coverage (all page types, industries, styles)?
- Would 200-500 deeply detailed patterns (with real tokens, real behavior, real code examples) outperform 7,000 shallow ones?
- What fields are actually useful vs noise?

### 7. How to validate that the MCP actually helps?
We need an honest test protocol:
- Same prompt, same model, with and without MCP
- Multiple prompts covering different page types
- Blind evaluation (someone rates the output without knowing which used MCP)
- Metrics: visual quality, accessibility score, code quality, adherence to design system

## Expected Output

A concrete plan with:
1. Data pipeline fixes (merge vision data, generate real tokens, improve descriptions)
2. New/modified MCP tools or tool responses that actually change AI behavior  
3. Quality-over-quantity strategy (trim and deepen vs keep all 7,080)
4. Validation protocol to prove it works
5. Implementation order (what to fix first for maximum impact)
