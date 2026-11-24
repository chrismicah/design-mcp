# Independent review of the revised dispositions

Reviewed by GPT-6.2 Sol (`a33acea8`) against corpus commit `82fe6e3` and scorer commit `a5fcd54`. A separate Claude Opus 5.5 session authored the scorer. I read the actual packaged data for 17 pattern rows and five supplemental records. This is a small, stratified source review of disposition quality. Visual taste remains limited to the two assets in the earlier sample.

## How to repeat the sample

Read `patterns_scored.csv` and join `id` to the full row in `design_mcp/data/patterns.json`. Sort each pool by ID, then use a single Python `random.Random(20261121)` to draw the pools in this order. Cull WebUI ×2, cull Dribbble ×2, conditional cull ×3, merge ×3, rewrite ×1 per source in Awwwards, Landbook, curated, Dribbble order, then reference ×3. Continue from the same random state for the supplemental sample, sorting within each pool by file and key. Draw rewrite ×1, reference ×2, cull ×1, then invalid-values fix ×1. The table identifies every drawn row.

## Pattern results

| Packaged row ID | Stored disposition | Evidence read and independent judgment |
| --- | --- | --- |
| `webui7k-1657129622990` | Cull | The record is a 404 titled “404 Not Found” with boilerplate hero copy, a layout placeholder and no asset. Agree. |
| `webui7k-1656106198918` | Cull | Classified as an admin panel with generic content-focused behavior, no code and no source asset. Agree. |
| `dribbble-26085147-Daily-UI-404-Page-Dark` | Cull | The title describes a deliberate 404 design, but the record offers a public shot link and a repeated content description. Agree on runtime exclusion. Retain provenance for potential recapture. |
| `dribbble-26504105-Project-Settings-Page` | Cull | Generic dashboard copy and a template reference supply no concrete settings interaction. A shot link remains as a potential source. Agree on runtime exclusion. |
| `screenshot-dribbble-2aaf777d7d` | Conditional cull | Missing local screenshot with an opaque ID and generic landing-page metadata. Agree. |
| `screenshot-dribbble-9ed3f54dca` | Conditional cull | Missing local screenshot, generic portfolio copy, and a landing-page template. Agree. |
| `screenshot-dribbble-2037f2e7b5` | Conditional cull | Missing local screenshot and the repeated hero prescription. Agree. |
| `awwwards-1820-productions` | Merge | Its award slug matches the archived capture name on `screenshot-awwwards-32b273f4a6`, with conflicting page types (Landing Page and Agency). Merge candidate. Reconcile category and preserve both source pointers. |
| `awwwards-ciridae` | Merge | Its award slug matches the archived capture name on `screenshot-awwwards-f385164e19`. Merge candidate. |
| `awwwards-gavin-schneider-productions` | Merge | Its award slug matches the archived capture name on `screenshot-awwwards-0f9ca3cc76`, with conflicting page types (Landing Page and Portfolio). Merge candidate. Reconcile category from the verified source. |
| `screenshot-awwwards-a033a7b011` | Rewrite from source | Cartier Watches Wonders 2025 has an identifiable subject and a missing local asset, with generic CTA copy. Agree on considering a rewrite after source verification. |
| `screenshot-landbook-49f9b839df` | Rewrite from source | Swim Club has an explicit orange/ink/white palette and generic product-grid copy, with a missing local asset. Agree on conditional rewrite. The palette alone does not establish the layout or behavior. |
| `screenshot-curated-6181206634` | Rewrite from source | Turso has identifiable subject matter and a missing local screenshot. The near-full-viewport stack description contains no proof it reflects the source. Agree on conditional rewrite. |
| `screenshot-dribbble-8c154a230c` | Rewrite from source | Sales Analytics Dark includes a three-color palette and generic dashboard copy with a missing local screenshot. Agree on conditional rewrite. |
| `seed-linear-dashboard` | Keep as reference | A collapsible 200 px rail and command-palette overlay are reusable ideas. Treat palette and specific product behavior as unverified until observed. |
| `seed-marketplace` | Keep as reference | The 260 px filter sidebar and responsive grid are concrete structural examples. Its `example.com/marketplace` URL makes this a synthetic example. Label it accordingly and keep it out of observed-source citations. |
| `seed-stripe-dashboard` | Keep as reference | A 240 px rail, 24 px grid gap and responsive collapse are useful ideas to test. Confirm the source before describing these as observed Stripe behavior. |

Across all 26 merge proposals, the published URL slug and historical screenshot filename stem match after lowercasing and removing non-alphanumeric characters. This supports the site pairing. The original assets may represent different captures of the same site, so check provenance and observed fields before consolidation.

## Supplemental results

| File and key | Stored disposition | Evidence read and independent judgment |
| --- | --- | --- |
| `tokens/token_sets.json` → `99` | Rewrite | This rust and cyan palette repeats the global type, gap and radius scale and includes no type families. Preserve useful role contrast for evaluation and create a direction for the task. |
| `anti_generic_system.json` → `component_code.secondary_kpi_dark` | Keep as reference | Inline value/delta and tabular numerals can help a dense screen. Three same-size stat cards and 10 px muted labels need layout and readability review before implementation. |
| `anti_generic_system.json` → `elevation_system` | Keep as reference | Names surface roles for the focal KPI, table and sidebar. The specific values apply to the documented dark example and still require contrast checks in a new screen. |
| `component_code.json` → `HeroSection` | Cull | Supplies a centered headline with placeholder copy and two generic buttons. Agree. |
| `anti_generic_system.json` → `color_overrides` | Fix invalid values | Values such as `#zinc-200` are neither hex colors nor valid utility names in this field. Agree. |

The sampled actions remain appropriate for triage. The review adds two execution checks. Distinguish synthetic reference examples from observed sources, and retain and reconcile capture metadata on each proposed merge. No scored row was promoted to a launch-ready direction.
