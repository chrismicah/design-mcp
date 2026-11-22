# Design MCP benchmark

The baseline pins Design MCP at `fd6035d8732d177b811f81a0f5863e99134a85ca`. The control runs the same generator with no MCP. The 36 briefs include six each for landing pages, dashboards, forms, mobile web, settings and empty states. The historical `master` revision and the earlier six-brief study are separate comparisons. [Tasks](evals/v1/tasks.json) · [Earlier study](evidence/rebuild/comparison/README.md)

## Baseline scoreboard

| Configuration | Judged pairs | Score / 100 |
| --- | ---: | ---: |
| Same generator without MCP | 30 / 36 | 92.4 |
| Same generator with Design MCP v2 | 30 / 36 | 94.9 |

The 30 verified pairs yielded a **+2.5-point** mean difference, with 17 wins, nine ties, four losses, and a paired bootstrap interval of 0.6 to 4.3 points. The judged set covers all six briefs in each of landing pages, dashboards, forms, mobile web, and settings. The maintenance form lost 95.8 to 83.3 after its illustration pushed the fields down and its Building hint clipped. The pantry collection screen lost 95.8 to 87.5 with transit typography and no text label for the address. Five other mobile briefs improved. Settings produced three wins, a tie, and two losses. The reading and digest screens each lost 100.0 to 95.8 when a prominent preview or saved schedule took priority over the controls. The judges used captured states under the original benchmark rubric. The release rubric requires live evaluation. [Paired ballots, hashes and token receipts](evidence/benchmark-v1/paired-progress.json) · [Release rubric](evals/vision/rubric.md)

The first dashboard attempt called `direct` successfully and reached the client’s 240-second timeout before returning HTML. There was no completed-turn token receipt. The paired run uses a 900-second allowance for both arms and retains the first attempt separately. Playwriter MCP `0.12.0` rendered the isolated Chrome 157 control at both widths. The injected failure control detected narrow viewport overflow and the expected JavaScript error. [Tracked receipts](evidence/benchmark-v1/preflight.json)

GitHub’s standard macOS runner captured the judged pairs with Playwriter 0.12.0 and Chrome for Testing 158.0.8127.36 at both preset widths. Across 120 judged captures, Playwriter recorded zero page errors and zero instances of document-level horizontal overflow. The maintenance hint clipped within its field. [First run](https://github.com/chrismicah/design-mcp/actions/runs/44984687051) · [Second run](https://github.com/chrismicah/design-mcp/actions/runs/44988686124) · [Third run](https://github.com/chrismicah/design-mcp/actions/runs/44991749251) · [Fourth run](https://github.com/chrismicah/design-mcp/actions/runs/44995146562) · [Fifth run](https://github.com/chrismicah/design-mcp/actions/runs/44998013520) · [Sixth run](https://github.com/chrismicah/design-mcp/actions/runs/45001223462)

An interaction replay on the exact maintenance pages passed all four arm-by-viewport checks. Empty submission focused the invalid Building field. Keyboard entry and urgency selection produced a local confirmation with the supplied details. Editing restored focus and retained every value. At 390 px the frozen v2 hint measured 124 px of text in 93 px of available space. Its first field began 110 px lower than in the plain layout. The form candidate must fix the geometry and preserve the workflow. [Keyboard and geometry receipts](evidence/benchmark-v1/maintenance-actions.json) · [Hosted replay](https://github.com/chrismicah/design-mcp/actions/runs/44992860729)

The exact pantry comparison pages both revealed and collapsed Details with Enter and kept focus on the control at 1440 and 390 CSS px. The day, time, and address stayed in the first viewport. The plain layout gave the address a text label in both views. The frozen v2 page used a pin icon and the address. Revealing the instructions loaded one permitted font resource on that page. [Keyboard replay and capture hashes](evidence/benchmark-v1/collection-baseline-actions.json)

Both frozen notification settings pages restored their two changed switches and the saved browser record after reload at 1440 and 390 CSS px. A seeded control displayed the same Saved message and lost both values. The first replay wiped storage during every navigation, invalidating its reload result. The corrected replay used identical HTML and kept storage through reload. [Saved and reopened hashes](evidence/benchmark-v1/settings-persistence.json) · [Hosted replay](https://github.com/chrismicah/design-mcp/actions/runs/45000936717)

Both display settings pages updated the date and temperature independently by keyboard and restored the initial formats when reset. Both supplier digest pages hid the day selector from view and tab order for Daily and Off, restored it on Weekly, and saved the expected summary in all three states. All eight checks passed across the two apps, both arms, and both widths. [Interaction and capture hashes](evidence/benchmark-v1/settings-preview-actions.json)

| Median per judged brief | Input tokens | Cached input | Output tokens | Seconds |
| --- | ---: | ---: | ---: | ---: |
| Plain generator | 20,545 | 11,136 | 20,257 | 408 |
| Design MCP v2 | 64,390 | 41,472 | 20,811 | 423 |

## Direction coverage

A separate stdio probe supplied the exact briefs to `direct` with the surface omitted. All 36 calls returned a direction. **32/36 returned `object-hero`.** All six forms and all six settings briefs received landing-page guidance. Only two dashboards and one mobile brief matched their requested surface. The production API has no form, settings or empty-state surface. This probe measures default retrieval, while the rendered comparison measures what the generator does with the tool available. [Per-brief direction returns](evidence/benchmark-v1/preflight.json)

## Installation at the baseline revision

Clean detached checkout on macOS 26.5.2, Apple Silicon. The smoke tests send real MCP requests from an isolated client to the installed executable. The pinned source suite passed 308 tests on Python 3.12.13.

| Installation | Actual interpreter | Result |
| --- | --- | --- |
| pipx | 3.12.13 | 17/17 tools in `both`, 14/14 in `legacy`, 3/3 in `v2` |
| uv | 3.13.3 | 17/17 tools in `both`, 3/3 in `v2` |
| pipx with explicit Python 3.10.20 | 3.10.20 | Package metadata rejected it with `>=3.12` |
| uv with `--python 3.10` | 3.12.13 | Installer selected a compatible interpreter |

The hosted macOS 15 install matrix passed all four jobs. Both installers served 17/17 tools in each arm64 and Intel job on Python 3.12 and 3.13. macOS 13, Python 3.10–3.11, and a fresh Tart VM remain open. [Hosted jobs](https://github.com/chrismicah/design-mcp/actions/runs/44984617955) · [Tracked local preflight](evidence/benchmark-v1/preflight.json)

The integrated development package subsequently passed eight clean-install jobs using the documented Git URL with both pipx and uv. Both installers recorded the expected Git commit in workspace-isolated environments. Each job exercised `doctor`, three default tools, all 17 compatibility tools and the bundled extension and desktop reviewer entry points. The matrix covers macOS 15 on both architectures and Python 3.10–3.13. Fresh Ventura remains open. [Exact commit and job receipts](evidence/benchmark-v1/direct-git-install.json)

## How the score is calculated

The harness runs each brief in two fresh sessions with matching model, effort, prompt, tool restrictions and allowed assets. The treatment must complete a `direct` call. The control uses an empty MCP configuration. Each cell records the client version, exit status, prompt hash, tool calls, elapsed time and provider-reported token fields. The receipt keeps input, cached input and output counts as reported by the client. [Generator](evals/v1/generate.py)

Playwriter opens each page in isolated Chrome and saves the first viewport at 1440 × 900 and 390 × 844. The harness records active web fonts, horizontal overflow, language, page errors and an accessibility-tree excerpt. Page content is served only on loopback, with external requests limited to the two Google Fonts origins. [Renderer](evals/v1/render.py)

The LLM judge sees the brief, browser observations and four screenshots for each pair, with shuffled anonymous labels. Hierarchy, spacing, typography, color, accessibility and fidelity each count equally. The report gives the mean paired difference, wins, ties and losses, a paired bootstrap interval, and the status of every cell. Accessibility scores describe what the available browser evidence can show. [Rubric](evals/v1/rubric.md) · [Judge](evals/v1/judge.py)

## Candidate decisions

| Candidate | Observed change | Status |
| --- | --- | --- |
| Form directions, `d5a3278` | The six form briefs went from 0/6 to 6/6 correct surface routes. The unchanged 36-brief diagnostic returned `object-hero` on 26/36, down from 32/36. The blind average rose from 91.0 to 92.4, with four wins and two losses. | Separate branch. The return label and exhibition briefs each fell from 91.7 to 87.5. Fix phrase breaks in titles, fieldset legends and ranges before promoting shared form guidance. [Source results](evidence/benchmark-v1/form-candidate-source.json) · [All six blind ballots](evidence/benchmark-v1/form-six-blind.json) |
| Form measure repair, `9856a23` | Return label improved from 87.5 to 95.8 in the rematch. Exhibition tied its paired control at 91.7. The two rematches averaged 93.8 versus 89.6 for the frozen controls. | Integrated at `453cfd3`. All eight keyboard replays passed through confirmation and edit. Exhibition's frozen control received 95.8 in its original ballot. The combined candidate `264cf6c` changed only the six form routes and passed all eight macOS 15 install jobs on arm64 and Intel. [Audited rematch ballots](evidence/benchmark-v1/form-measure-visual.json) · [Live keyboard receipts](evidence/benchmark-v1/form-measure-actions.json) · [Route replay](evidence/benchmark-v1/form-rollout-route-parity.json) · [Install CI](https://github.com/chrismicah/design-mcp/actions/runs/45000311068) |
| Broadcast and service booking, `384d61d` | Two matched blind comparisons averaged 89.6 for the frozen v2 and 97.9 for the candidate. Radio scored 87.5 → 95.8. Bike booking scored 91.7 → 100.0. Four other landing briefs kept their original direction in the six-call replay. | Integrated at `9756a34`. All eight browser keyboard checks passed across both arms and widths. All six integrated direction replies matched the candidate, the 17-tool stdio smoke passed, and the source suite passed 338 tests. [Paired visual scores](evidence/benchmark-v1/specific-landing-visual.json) · [Browser actions](evidence/benchmark-v1/specific-landing-actions.json) · [Integrated stdio and tests](evidence/benchmark-v1/specific-landing-integration.json) |
| Mobile product hero, `9de7829` | On the matched ceramics brief, the candidate scored 95.8 against 87.5 for frozen v2. The critique identified tighter mobile grouping of the artwork, price, shipping time and purchase action. | Integrated at `5cc8074`. Both builds added one bowl, opened the bag and restored keyboard focus at both widths. The integrated source passed 338 tests and 17 stdio calls. The fresh coffee and train comparison is separate. [Visual and interaction receipts](evidence/benchmark-v1/product-hero-visual.json) |
| Portable package and doctor, `7caf890` | Package resources and a checksum-pinned legacy cache support Python 3.10–3.13. The 36 directions, 21 reactions and one source check had identical normalized replies on Python 3.12. | Integrated on the rebuild branch. All eight macOS 15 jobs passed with pipx, uv, `doctor`, and all 17 tools on Intel and arm64. macOS 13 and fresh Tart remain open. [Output parity](evidence/benchmark-v1/portable-parity.json) · [Final hosted jobs](https://github.com/chrismicah/design-mcp/actions/runs/44987155008) |
| Collection details, `cf1b567` | Two generator paraphrases fell back to transit signage with earlier classifier revisions. The first output scored 87.5 against 91.7 for the plain control. The trace gate stopped the second before rendering. | Astra reviewed the task classification. The replacement passed both exact requests over stdio, 63 direction tests, and 245 unchanged responses for the other 35 briefs. One matched visual rerun is pending. [Actual tool calls](evidence/benchmark-v1/collection-details-candidate.json) · [Stdio and route replay](evidence/benchmark-v1/collection-visit-route-parity.json) |

The train layout repair scored 95.8 against 87.5 for both fresh controls. It passed live ticket reveal and collapse at both widths and was integrated at `a7d1019`. The coffee repair beat fresh v2, 100.0 to 91.7, and passed the keyboard purchase replay. Its layout is already included in the mobile product direction. Against the exact historical install, train scored 95.8 to 87.5 and coffee tied at 95.8. The historical comparison used three read-only legacy tools and the same prompts, generator, browser, and blind rubric. [Fresh v2 ballots](evidence/benchmark-v1/pilot-repair-vs-v2.json) · [Historical ballots](evidence/benchmark-v1/pilot-repair-vs-legacy.json) · [Interactions and integration](evidence/benchmark-v1/pilot-repair-actions.json)

All four candidate keyboard replays passed. At 1440 and 390 CSS px, axe found zero contrast violations before or after the action. Paired rendered backgrounds resolved its 20 incomplete checks on the coffee illustration and train platform sign. The dispatcher returned the same structured direction from the pilot and curated candidate, and the archived desktop and mobile actions still identify the delayed load. [Contrast and dispatcher receipts](evidence/benchmark-v1/pilot-repair-contrast.json)

The repaired maintenance form passed keyboard validation, local confirmation, and editing at 1440 and 390 px. Both frozen controls repeated those functional passes. At 390 px the repair brings the first input from 459.8 to 290.3 CSS px and removes the clipped Building placeholder. This fits all controls within the first capture. The workshop candidate and frozen v2 both passed keyboard selection, invalid-email recovery, local confirmation and editing at both widths. The maintenance comparison against the plain generator is separate. [Maintenance actions](evidence/benchmark-v1/form-candidate-maintenance-actions.json) · [Workshop actions](evidence/benchmark-v1/form-candidate-venue-actions.json)

The final portability candidate also returned the same structured results as the frozen baseline for all 17 stdio smoke calls at each of two fixed Python hash seeds. The comparison and library tools vary their ordering with the seed in both versions. The matched test verifies the package change independently of that existing behavior. [Stdio parity receipt](evidence/benchmark-v1/portable-stdio-parity.json)

Apply the same prompts, asset policy and scoring to each candidate. Preserve failed runs and report coverage alongside quality and tokens.

Both specific-landing v2 controls were scored again alongside the candidate. Their rescored values differ from the earlier v2-versus-plain ballots. Use the scores within each pair for candidate decisions. Both comparisons used the original benchmark rubric for captured states.

## Local review checks

The local reviewer now detects large text below WCAG's 3 to 1 minimum and keeps the 4.5 to 1 check for smaller text. Three boundary cases failed before the change and passed after it. Installed Chrome reproduced the large-text finding, showed a 3 to 1 recolor, and let a keyboard user switch the preview to After. The original small-text flow and field masking passed in the same CI run. [Regression and browser receipts](evidence/benchmark-v1/large-text-contrast.json) · [WCAG contrast requirements](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

## Compact vision experiment

Across two briefs, the compact packets used 48,695 input tokens versus 51,112 with full screenshots, a 4.7% reduction. The theatre comparison kept both scores. The ceramics comparison moved from a tie to a 4.2-point lead for the plain generator. The compact run changed image size and supplied region measurements, so this comparison cannot isolate either change. Keep the full-size packets for the benchmark and measure region detection, decision agreement, and token savings on unseen examples before using compact packets by default. [Blind ballots and usage](evidence/benchmark-v1/compact-vision.json)

The controlled theatre replay used identical region facts and the same before and after interaction evidence in two anonymous packets. One packet had four original images. The other used a 696 × 744 contact sheet. Both critics identified the oversized title as the highest-priority hierarchy problem and confirmed Studio B remained at both widths. The sheet used 21,043 input tokens against 24,546 for the originals, a **14.3% reduction**, below the 40% gate. Keep full-size release evidence and test whether local findings reduce the need for frontier calls. [Controlled ballots, image hashes, and usage](evidence/benchmark-v1/vision-packet-ablation.json)

The cached Playwriter action receipt answered the filter question at both widths without inference. The named row locators, count announcement, and pressed state agreed that only Studio B remained. The replay withheld an answer for all six injected contradictions and missing states. Hierarchy remains a full-image judgment. The original model call combined both questions, so this replay does not estimate token savings for a combined critique or qualify general dispatch. [Deterministic check](evals/vision/replay_frontier_dispatch.py) · [Replay evidence](evidence/benchmark-v1/frontier-dispatch-replay.json)

## Competitor search coverage

All four pinned credential-free tools were installed in CI and called on all 36 original briefs. Three returned matches for every brief and Design Library's keyword mode returned none when given the full brief. The earlier keyword preflight yielded a settings result, so the generator comparison allows the agent to choose search terms. On the frozen ceramics brief, Design MCP scored 91.7 against 87.5 for hosted Inspo and tied Offline Designer at 91.7. In a fresh shell-disabled comparison on that brief, Design MCP scored 95.8 against 87.5 for Design Library. The Screenshots attempt produced no MCP call and has no visual ballot. [Retrieval and visual scoreboard](teardown/COMPETITORS.md#visual-scoreboard) · [Shell-disabled rematch](evidence/benchmark-v1/competitor-shell-disabled-rematch.json)

Two additional pinned installs received the same 36 unedited briefs. UI UX Pro Max returned matches on 23 and shadcn's official registry returned none. Both found their respective short positive controls and returned empty for nonsense. Visual generation remains unmeasured for these two configurations. [Per-brief retrieval results](evidence/benchmark-v1/registry-and-skill-retrieval.json)
