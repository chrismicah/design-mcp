# AUDIT — Design MCP runtime, ranking, schema, docs, install

Commit audited: `82fe6e3` (branch `chrismicah/content-quality-audit`, equal to `origin/master` at fetch).
Author: coordinator session `eb3116f5` (Claude Fable 5.2). Status: **pre-approval.** Independent verification and limits are recorded in §9.
Scope of this file: the 14 runtime tools, ranking/selection, schema, docs, install. The [per-entry corpus audit](CONTENT-AUDIT.md) and [research](research/) are companion deliverables.

This audit records the starting revision. The [benchmark](EVALS.md) and [smoke receipts](SMOKE-RECEIPTS.md) track the rebuilt server, current verification, and outstanding release checks.

## 0. Verdict

The server does not do the job in the brief. One call cannot return a distinctive, art-directed direction, because no tool selects a direction: search is keyword overlap on a corpus that is 85% undifferentiated landing pages, and the "design system" tool returns the same Inter-based dark-SaaS kit for every non-dashboard page type. The critique tools miss every banned tell in a sample built from the banned list and then recommend Inter and `#3b82f6` as the fix. A default search returns 86k–169k characters of JSON (roughly 21k–42k tokens at 4 characters per token; no tokenizer was run), and about 80% of each result is the embedded recipe and design-system kit.

Keep: the packaging entry point, the WCAG palette generator, the behavioural templates as a seed, the curated/Awwwards subset as candidates for the corpus audit. Replace: ranking, schema, tool surface, the anti-generic kit, the critique rules, the README.

## 1. Proof files

Compact proofs are in `evidence/runtime/` (see its `README.md`), with local paths redacted. Raw per-call outputs stay untracked under `.context/audit/coordinator/probe-source/` and `probe-installed/`; `probe.py` regenerates them. Row citations of the form `search_*.json` refer to those raw files; the figures quoted from them are also in the summaries. Sizes are character counts of serialised JSON, and token figures are that count divided by 4.

| Ref | File | What it is |
|---|---|---|
| P1 | `evidence/runtime/probe.py` | Read-only harness: imports `design_mcp.server`, calls every tool, writes one JSON per call |
| P2 | `evidence/runtime/summary-source.json` + 69 untracked per-call files | Run against the worktree source |
| P3 | `evidence/runtime/summary-installed.json` + untracked per-call files | Same harness against the pipx-installed build (`server.py` sha `951de4b9…`, identical to source) |
| P4 | `evidence/runtime/tool-inventory-source.json` | Tool listing as a client receives it: names, params, description and schema sizes |
| P5 | `evidence/runtime/facts-source.json` | Corpus distributions, payload byte breakdown, taxonomy mismatches |
| P6 | `evidence/runtime/slop-detection.json` | What the critique tools found in the banned-tell sample |
| P7 | `evidence/runtime/docs-install-facts.txt` | README claims against repo facts, unpackaged imports, stray files |
| P8 | [installed-stdio.json](evidence/runtime/installed-stdio.json) | Independent stdio handshake, tool list and custom-color check from a temporary directory |
| P9 | [baseline-pytest.log](evidence/runtime/baseline-pytest.log) | Existing root suite, 297 passes and one missing-screenshot failure |

Caveat on P2/P3: the `slop_sample_detection` field in `summary.json` is a substring check that also matches echoed input. Do not cite it; P6 supersedes it.

## 2. Tool-by-tool findings

14 tools are registered (`design_mcp/server.py`, 14 `@mcp.tool()` decorators; P4). README documents 12 and omits `get_design_system` and `get_visual_recipe` (P7). The listing costs a client 12,659 characters of descriptions and schemas (P4). Seven tools have no required argument; nothing marks an entry point.

| # | Tool (line) | Works? | Finding | Proof |
|---|---|---|---|---|
| 1 | `search_design_patterns` (85) | Runs | 86k–169k characters of JSON per call at default `limit=5`. At 4 characters per token that is roughly 21k–42k tokens; actual token counts are unknown. `visual_recipes` (7.6 KB) and `design_system` (8.2 KB) are embedded in every result; that is 80% of a 19.8k-character result. `visual_recipes`, `decision_tree` and `accessibility_notes` are identical across the five results; `design_system` and `semantic_tokens` are not. Ranking: §3. | P2 `search_*.json`; P5 `search_result0_field_bytes`, `search_shared_boilerplate` |
| 2 | `get_design_blueprint` (133) | Inverted | `detailed=True` returns 3.6 KB; the default "condensed" form returns 27.3 KB, because only the condensed path adds the recipe and system boilerplate. | P2 `blueprint_condensed.json`, `blueprint_detailed.json` |
| 3 | `get_semantic_tokens` (167) | Broken when installed | `primary_color` is silently ignored in the installed build: the generator is imported from `scripts.rebuild_pipeline` (line 192), which is not packaged, and the `except Exception: pass` hides it. Source run honours the colour; installed run returns the default for any colour. Documented styles `brand`, `minimal`, `bold` return the same payload as no style. Default token set contains startup blue. | P3 `tokens` block (`primary_color_ignored_equals_default: true`) vs P2; P2 `tokens_style_*.json` |
| 4 | `get_design_taxonomy` (240) | Runs, wrong | Taxonomy lists 25 page types; the corpus uses 33. `Portfolio` (107 patterns), `Agency` (106), `SaaS` (82), `E-commerce` (68), `Corporate` (47) are absent from the taxonomy; `Invoice` and `Email Template` are listed with zero patterns. An agent filtering by a taxonomy value can get nothing, and cannot discover values that do exist. | P5 `pattern_page_types_not_in_taxonomy`, `taxonomy_page_types_with_zero_patterns` |
| 5 | `get_behavioral_pattern` (258) | Runs | 12 templates, ~500 bytes each. The six names in the docstring resolve. Behaviour only; no visual direction. Unknown names return an error plus the list, which is the right shape. | P2 `behavior_*.json` |
| 6 | `compare_design_approaches` (286) | Brittle | Exact, case-insensitive page-type match only: `"pricing pages"` returns "No patterns found". A successful call is 63.9 KB for three examples, same boilerplate as search. The "summary of key differences" is generated from templated fields (§4), so it cannot report real differences. | P2 `compare_pricing.json`, `compare_lowercase_plural.json` |
| 7 | `analyze_and_devibecode` (314) | Misses the target | On the banned-tell sample it reports three things: an inline style, a missing flex/grid class, and a missing `aria-modal` on a modal that is not in the sample. It classifies a hero as "Navigation Bar". It reports none of: Inter/system-ui, purple-to-blue gradient, the AI hero, the three-card grid, the glass nav, the banned copy, the emoji bullet. Response is 14.6 KB, mostly the generic recipe dump. | P6; P2 `devibecode_slop.json` |
| 8 | `get_design_system` (474) | Runs, generic | 12 calls across 6 page types × 2 colour modes produce 4 distinct outputs; `page_type` only switches on a data-heavy flag (line 528), so Landing Page, Pricing, Portfolio, Blog and Mobile App are identical. `aesthetic` accepts only five SaaS brand names (mercury, linear, vercel, stripe, notion; line 490); `editorial`, `brutalist`, `luxury`, `playful` are silently ignored. The font system it returns is `* { font-family: 'Inter', system-ui, sans-serif }` with Geist as the alternative. Defaults are `Dashboard` + `dark`. | P2 `design_system_distinct_outputs`, `system_*.json`; P5 `design_system_font_mentions` |
| 9 | `get_library_recommendations` (551) | Runs | Observed: returns shadcn/ui, Tailwind CSS and Framer Motion for a marketing landing page. Judgement (coordinator, not measured): these are the libraries most agents already reach for, so the recommendation adds no direction. No evidence here shows the stack itself causes generic output. | P2 `libs_default.json`; P5 `libs_default_names` |
| 10 | `get_library_details` (665) | Runs | Fine as a lookup; unknown names return an error with alternatives. | P2 `lib_details*.json` |
| 11 | `scan_project` (713) | Misleading | Scores the banned-tell sample **95.5/100** project health. Reads any path the caller passes, recursively, with no root restriction (lines 734–775). Docstring example is a Windows path. | P6 `scan_health_score`; P2 `scan_tmp_project.json` |
| 12 | `generate_refactored_code` (973) | Misnamed | Returns no code: keys are transformations, imports, and the recipe dump. 16.7 KB. | P6 `refactor_returns_code: false`; P5 `refactor_keys` |
| 13 | `get_visual_recipe` (1506) | Partial | Page types without a relevance mapping (`Blog`, `Mobile App`) fall through to the entire 12 KB recipe file. Recipes are restraint rules for dark SaaS surfaces; no type pairing, palette logic, layout skeleton, or motion spec per direction. | P2 `recipe_distinct_outputs`, `recipe_*.json` |
| 14 | `get_visual_suggestions` (1564) | Recommends the tells | Default `brand_style="clean_modern"` prescribes Inter for heading and body and derives the palette from `#3b82f6` (`FONT_PAIRINGS`, `models/visual_analyzer.py:479`). On the sample its top two "quick wins" are "add dark mode" and "vary font weights". Line 1616 imports `models.visual_analyzer` (unpackaged path), another silent-failure site when installed. | P6; P2 `visual_suggestions_slop.json`; P7 "unpackaged imports" |

No call raised an exception in either build (P2/P3 `errors: {}`). The failures are silent wrong answers, which is worse for an agent consumer than an error.

## 3. Ranking and selection

Code: `design_mcp/database.py:51-100`.

- Score = count of query words that occur as **substrings** of a concatenated text field. No tokenisation, stop-word handling, stemming, weighting, or field priority. The query `"a"` returns five results (P2 `search_stopword.json`).
- Stop-words swamp the signal. For "landing page for a specialty coffee roaster" and "analytics dashboard for a logistics company", 7,080 of 7,080 patterns score above zero (P2 `ranking.*.candidates_score_gt0`).
- Ties are large and are broken only by `quality_score`: 164 patterns tie at the top score for the portfolio brief, 24 for dashboard, 20 for pricing (P2 `candidates_at_max_score`). Output is deterministic, so every agent with a similar brief gets the same five references. That is convergence built into the server.
- Relevance failures on the six QA briefs (P2 `ranking`):
  - Coffee roaster landing page → two near-duplicate entries from one Vietnamese blog (`ourcoffeewithacause.net`), then Cartier, a Manhattan tower, and Aramco.
  - Mobile banking home screen → three onboarding flows and two unrelated landing pages.
  - Editorial food magazine → a WordPress freelancer's site, an "About" page returned twice under two ids, and "About Us – Harvest".
  - "make it look nice" → five unrelated results matched on "make", "it", "nice".
- `platform` defaults to `"web"` and the corpus is 100% web (P5 `platform`). `platform="ios"` or `"android"` returns `[]`. The schema, docstring and taxonomy all advertise mobile.
- There is no diversity constraint, no notion of direction or style family, no negative filtering of banned tells, no seed or variation control, and no "why this one". Selection cannot produce "one distinctive direction"; it can only return the top of a keyword tie.

## 4. Schema and data shape

Code: `design_mcp/schema.py`. Corpus facts: P5. (Entry-level quality is the corpus auditor's job; these are structural facts that bear on ranking and the tool surface.)

- 7,080 patterns: 6,134 from `webui-7kbal` (87%), 435 Dribbble, 331 Awwwards, 90 curated, 90 Landbook. 6,036 (85%) are typed `Landing Page`.
- `quality_score` is bimodal: the scraped bulk sits at 1.7–2.7, the curated and gallery entries at 7–9. Ranking uses it only as a tie-break, so a 1.9-scored scrape with one more stop-word hit outranks a 9.0.
- Metadata is templated, not observed: across 7,080 patterns there are 14 distinct `behavioral_description` values, 25 distinct `layout_notes`, 35 distinct `accessibility_notes`. `semantic_tokens` is an integer index for every pattern. `color_mode` is null for 6,199. `image_url` exists for 773.
- The schema has none of the fields the brief requires per pattern: type pairing, scale ratio, palette logic, layout skeleton, motion spec, rationale with citations. There is no provenance or licence field, no reviewer or audit status, no direction/family grouping, no "tells present" field.
- Enumerations encode the tells as first-class options: `LayoutType.HERO_CENTERED`, `CARD_GRID`; the `visual_style` description leads with "Glassmorphism".
- `README` claims behavioural descriptions on 97% of patterns; the field is populated on 100% but with 14 strings (P7, P5). The completeness table measures presence, not information.

## 5. The anti-generic layer contradicts the brief

`data/anti_generic_system.json` and `data/visual_recipes.json` are the product's current answer to slop. Their analysis of AI defaults is partly right (equal grids, uniform spacing), and `font_system._why` states "Font is the #1 tell of AI-generated UI". The remedy it then ships is Inter with `cv` features, Geist, zinc neutrals, and five named SaaS profiles (P2 `system_Landing_Page_light.json`). Against the banned list in the brief that is a single house style, and it is the one the brief bans first. Every search result and blueprint carries this kit (§2 row 1), so the more an agent uses the server, the more its output converges on it.

Tell counts in tool output, for reference (P2 `calls.*.tells`): each five-result search response contains 15 mentions of Inter, 5 of system-ui, 15–45 of "gradient", 20–24 of purple/indigo/violet; zero mentions of any display serif from the brief's "good" list.

## 6. Docs

- README says "MCP Tools (12)" and "server.py — 12 MCP tools"; 14 are registered (P7).
- Pattern count is "7,000+" in README and `pyproject.toml`, "6,300+" in the brief, 7,080 in data. `patterns.json` is 10.09 MB; README says 11.7 MB.
- README describes "742 high-res design screenshots" in Git LFS; one file is tracked under `screenshots/` (P7). Not verified whether the LFS objects exist on the remote.
- No guidance on which tool to call first, in what order, or what a good result looks like. The server `instructions` string is one generic sentence (`server.py:20`).
- Root carries a second, unshipped copy of the app (`server.py`, `schema.py`, `database.py`, `enrichment.py`, `models/`, `data/`, `prompts/`) plus `test_dashboard.html`, `test_trackr_v3.html`, `test_output.json`, `test_server.py`, `test_with_data.py`, `RESEARCH_PROMPT.md`, `DESIGN_DOC.md`. `data/` and `design_mcp/data/` are identical (≈11 MB duplicated); `models/` and `design_mcp/models/` have already drifted (P7).
- `database.py` docstring: "optimized for the 24-hour build timeline".

## 7. Install path

- The README install commands were **not** run. What was exercised: a pipx install already present on this machine, whose `server.py` hash equals this commit's, imports and answers all 14 tools in-process (P3). That shows the wheel layout can work. A separate session's `evidence/runtime/installed-stdio.json` shows the same existing executable completing an MCP `initialize` over stdio and listing 14 tools; it also independently reproduces the ignored `primary_color`. Neither run shows that `pip install git+…` or any client registration works from a clean state (§9).
- `requires-python >=3.12` is stricter than anything in the code appears to need; not tested on 3.10/3.11.
- `claude_desktop_config.json` in the repo root hard-codes an absolute Windows user-profile path to the root `server.py`. It will not work for anyone else and exposes a local account name.
- Two runtime imports point outside the package (`scripts.rebuild_pipeline`, `models.visual_analyzer`), so installed behaviour differs from source behaviour without an error (§2 rows 3, 14).
- Tests import the root copies (`from server import`, `from schema import`, `from database import`), not `design_mcp.*` (P7). A green suite therefore says nothing about the shipped package. No CI config exists.
- `enrichment.py` ships in the package, calls the Anthropic API with a hard-coded 2025 model id, and needs `ANTHROPIC_API_KEY`. It is not reachable from any tool; it should not be in the runtime wheel.
- Cold import loads and validates 7,080 Pydantic models from a 10 MB JSON in about 0.4 s (P2 `import_seconds`). Acceptable; `get()` is a linear scan.

## 8. What is missing, against the brief

1. A single obvious entry call that turns a vague brief into one specific art direction (type pairing, scale, palette logic, layout skeleton, signature motion, copy voice, rationale).
2. Any mechanism for variation or anti-convergence: direction families, seeded choice, exclusion of what was just used.
3. A reaction loop: zero to two multiple-choice questions with a strong default, and one-word reactions that make a predictable change (addenda, "Taste and target user").
4. Banned-tell detection that matches the banned list, usable as a test oracle and by reviewers.
5. Per-pattern art-direction metadata and citations to research.
6. Mobile coverage, or an honest statement that there is none.
7. Response budgets. Nothing bounds payload size.
8. An eval harness: fixed prompt set, scored outputs, regression gate.

## 9. Independent verification and limits

- The installed executable reports package version 0.1.0, advertises MCP server version 3.1.0, lists 14 tools over stdio and returns the same token payload for the default and a request with `primary_color=#793C22`. It was run outside the checkout against the existing installation. Fresh clone, clean install, and real-client configuration are still smoke-test requirements. [Stdio receipt](evidence/runtime/installed-stdio.json)
- The baseline suite ran with Python 3.13.3, the installed runtime dependencies and locally available pytest support. **297 passed, one failed.** `TestDataQuality.test_screenshot_files_exist` expected at least 100 screenshot files and found only the guide. These tests use the root copies. [Test log](evidence/runtime/baseline-pytest.log)
- The audit's tell counts reflect regexes over tool responses. Published reference imagery was inspected for research. Rendered baseline, rebuilt UI, competitive outcomes and mobile usability remain for evaluation. [UI source evidence](evidence/research/UI-SOURCES.md)
- This checkout contains no historical screenshot blobs or identifiable “Tyre” source. The remote LFS object store was outside the check. [Source material audit](evidence/content/REFERENCE-MATERIAL.md)
- Model token totals were unavailable in the task tools. [Ledger](LEDGER.md)

## 10. Corpus disposition

The corpus review found 14 distinct behavioral descriptions across 7,080 entries, 6,555 placeholder layout notes, and 5,665 entries that use the same token set. Zero patterns qualify for the new direction library as written. The cull list and rewrite candidates are proposals based on the available entry content. Pixel-level judgment covers the recovered sample. Every new or rewritten direction still needs observable evidence and reviewer approval. [Content audit](CONTENT-AUDIT.md) · [Row-level action list](evidence/content/action_list.csv)

All 742 historical vision-analysis keys join to runtime rows. Of those, 733 match every original field and nine differ in `ui_elements`. [Vision reconciliation](evidence/content/vision-reconciliation.json)
