# Judged sample: read-through vs heuristic

Reviewer: Claude Opus 5.5 (session 419b2a67), 2026-11-20. One model read each record, so these are **one model's judgments, not independent human taste**. Sample: seeded stratified draw (`random.seed(20261120)`, ids in `.context/sample_ids.json` at audit time), plus the two rows whose remote assets could be fetched and viewed. Every field quoted below comes from `design_mcp/data/patterns.json` (or the named supplemental file) at commit 82fe6e3.

## Patterns (22 rows)

| # | id | Heuristic action | Read-through verdict | Agree | Evidence |
|---|----|------------------|----------------------|-------|----------|
| 1 | seed-docs-page | keep | rewrite | no | accent `#3b82f6` (Tailwind blue-500, the "startup blue" tell); a stock 3-column docs layout with no type direction |
| 2 | seed-file-explorer | keep | rewrite | no | Google Drive palette `#1a73e8/#5f6368`; description is the 509×-shared "Content-focused layout…" |
| 3 | seed-profile-page | keep | rewrite | no | Twitter palette `#1da1f2/#657786`; same 509× description |
| 4 | seed-admin-panel | keep | rewrite | no | `#3b82f6` accent; generic sidebar plus table |
| 5 | screenshot-curated-84f7ada512 (Laravel) | rewrite | rewrite | yes | source worth keeping; `layout_notes` = `[template:Landing Page]` |
| 6 | screenshot-curated-b75efa9a29 (Upstash) | rewrite | rewrite | yes | 74× shared description |
| 7 | screenshot-awwwards-17386a4907 (Pendragon Cycle) | rewrite | rewrite | yes | tagged 3D/Dark/Futuristic but described as the 5,823× "Large headline with subtext and primary CTA" hero: the text contradicts the tags |
| 8 | screenshot-awwwards-b42cdb8d28 (Seriti Films) | rewrite | rewrite | yes | Editorial agency site given the 509× generic text |
| 9 | screenshot-awwwards-aa48c6f430 (Casa Lunara) | rewrite | rewrite | yes | e-com grid boilerplate; can't be checked without the blob |
| 10 | screenshot-awwwards-4d59ad7ad1 (22 09 2000) | rewrite | rewrite | yes | portfolio boilerplate (107×) |
| 11 | awwwards-1820-productions | merge-duplicate | merge | yes | same site exists as a screenshot row |
| 12–14 | screenshot-dribbble-cf28eb672f / -201967e584 / -c9a98842b4 | rewrite | **cull unless blob recovered** | partial | names are hex ids (`Dc6E40163E5C`), the blob is absent, and the text is boilerplate, so nothing usable is left |
| 15 | screenshot-landbook-fa291ce05a | rewrite | rewrite | yes | 509× text |
| 16 | screenshot-landbook-29e94fbf31 (Quinn Global) | rewrite | rewrite | yes | only real signal is extracted colours `#3B2E1E/#D4893E` |
| 17 | webui7k-1656551480478 (React Native newsletter sponsor) | cull | cull | yes | crawl row with 5,823× text; no asset |
| 18 | webui7k-1658334330808 (Chinese SEO-spam title) | cull | cull | yes | spam page labelled "Landing Page" |
| 19–20 | webui7k-1658752409067, -1655971721440 | cull | cull | yes | both named "404 Not Found" |
| 21 | awwwards-studio-dado (**asset viewed**) | merge-duplicate | **keep source, rewrite text; strongest example** | partial | the real page has a serif display "FORM FOLLOWS FEELING" set full-bleed over warm interior photography, an offset grid and a tiny sans for UI. The DB calls it the AI hero ("Large headline with subtext and primary CTA… hover glow… staggered fade-in") and assigns token set 3, primary `#6366f1` indigo |
| 22 | awwwards-voku-studiotm (**asset viewed**) | rewrite | rewrite | yes | the real page has an arc of image tiles on a white card over a blurred blue field, with a one-line nav and **no headline or CTA**. The DB text claims "Large headline… primary CTA". It is factually wrong |

Agreement: 15 of 22 agree outright, 3 partially, and 4 disagree. **Every disagreement shows the heuristic was too lenient.** The 4 rejected "keep" rows are the hand-written `seed-*` rows: they have specific `layout_notes` but copy big-brand palettes and use blue-500. I therefore downgrade all 20 heuristic `keep` rows to **rewrite** in the final cull list. The heuristic cannot see brand-copy palettes, and blue-500 is only weakly penalised (it appears in 142 token sets as `color-info`, so penalising it hard would penalise everything).

## Supplemental (13 records)

| Record | Heuristic | Verdict | Agree | Evidence |
|--------|-----------|---------|-------|----------|
| component_code.json › HeroSection | rewrite | **cull/rewrite (worst example)** | yes | `max-w-2xl text-center`, "Your headline here", "A compelling subheadline…": this is the banned AI hero verbatim |
| layout_templates.json › Landing Page | rewrite | rewrite | yes | centered hero, `text-center`, "Headline" |
| behavioral_templates.json › Portfolio | rewrite | rewrite (light) | yes | sensible ("work speaks", 200ms hover) but has no type, palette or art direction |
| behavioral_templates.json › Dashboard | keep | keep | yes | specific: `text-[2.5rem] tracking-[-0.03em]`, "NEVER equal width" |
| anti_generic_system › spacing_system | keep | **rewrite** | no | locks every section gap to `mt-5` (20px). Dashboard density forced everywhere contradicts "big empty space as a feature" |
| anti_generic_system › color_overrides | keep | **fix** | no | invalid hex values `#zinc-200…#zinc-700` (5) |
| anti_generic_system › elevation_system | keep | keep, scoped to dark dashboards | yes | 2–3% lightness steps; genuinely non-default |
| anti_generic_system › composition_rules | keep | keep, scoped | yes | hero KPI then 3 secondary; strong, but only covers dashboards |
| anti_generic_system › font_system | rewrite | rewrite | yes | `root_css`: `font-family: 'Inter', system-ui` on `*` (banned tell, applied globally) |
| aesthetic_profiles × 5 (mercury/linear/vercel/stripe/notion) | rewrite | rewrite | yes | 4 of 5 use Inter/system-ui and all 5 are near-black SaaS dashboards: one aesthetic under five names |
| tokens/token_sets.json (141) | rewrite | rewrite | yes | type scale, spacing and radius are byte-identical across all 141 sets, no font family is set, and only the colours vary |
| visual_recipes › color_restraint | rewrite | keep principle, rewrite examples | partial | the restraint principle is right, but every exemplar is a SaaS dashboard |
| libraries.json (18) | keep-as-reference | keep-as-reference | yes | factual catalogue, not taste content |

Agreement: 10 of 13 agree, 1 partially, 2 disagree. Again the disagreements say the heuristic was too lenient.
