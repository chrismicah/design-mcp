# Design MCP benchmark

The baseline pins Design MCP at `fd6035d8732d177b811f81a0f5863e99134a85ca`. The control runs the same generator with no MCP. The 36 briefs include six each for landing pages, dashboards, forms, mobile web, settings and empty states. The historical `master` revision and the earlier six-brief study are separate comparisons. [Tasks](evals/v1/tasks.json) · [Earlier study](evidence/rebuild/comparison/README.md)

## Baseline scoreboard

| Configuration | Judged pairs | Score / 100 |
| --- | ---: | ---: |
| Same generator without MCP | 12 / 36 | 92.0 |
| Same generator with Design MCP v2 | 12 / 36 | 95.8 |

The twelve verified pairs yielded a **+3.8-point** mean difference, with six wins, six ties, and a paired bootstrap interval of 1.4 to 6.3 points. Rehearsal rooms and the film festival each scored 91.7 → 100.0. Cold-chain monitoring scored 95.8 → 100.0. The judged set covers all six landing pages and all six dashboards. This is a partial baseline for the frozen revision. The judges scored captured states under the original benchmark rubric. The separate release rubric requires live evaluation before scoring. [Paired ballots, hashes and token receipts](evidence/benchmark-v1/paired-progress.json) · [Release rubric](evals/vision/rubric.md)

The first dashboard attempt called `direct` successfully and reached the client’s 240-second timeout before returning HTML. There was no completed-turn token receipt. The paired run uses a 900-second allowance for both arms and retains the first attempt separately. Playwriter MCP `0.12.0` rendered the isolated Chrome 157 control at both widths. The injected failure control detected narrow viewport overflow and the expected JavaScript error. [Tracked receipts](evidence/benchmark-v1/preflight.json)

GitHub’s standard macOS runner captured the judged pairs with Playwriter 0.12.0 and Chrome for Testing 158.0.8127.36 at both preset widths. All 48 judged captures had no horizontal overflow or page errors. The third wave also captured two form briefs. [First run](https://github.com/chrismicah/design-mcp/actions/runs/44984687051) · [Second run](https://github.com/chrismicah/design-mcp/actions/runs/44988686124) · [Third run](https://github.com/chrismicah/design-mcp/actions/runs/44991749251)

| Median per judged brief | Input tokens | Cached input | Output tokens | Seconds |
| --- | ---: | ---: | ---: | ---: |
| Plain generator | 20,084 | 0 | 19,616 | 404 |
| Design MCP v2 | 62,895 | 40,832 | 20,811 | 423 |

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

## How the score is calculated

The harness runs each brief in two fresh sessions with matching model, effort, prompt, tool restrictions and allowed assets. The treatment must complete a `direct` call. The control uses an empty MCP configuration. Each cell records the client version, exit status, prompt hash, tool calls, elapsed time and provider-reported token fields. The receipt keeps input, cached input and output counts as reported by the client. [Generator](evals/v1/generate.py)

Playwriter opens each page in isolated Chrome and saves the first viewport at 1440 × 900 and 390 × 844. The harness records active web fonts, horizontal overflow, language, page errors and an accessibility-tree excerpt. Page content is served only on loopback, with external requests limited to the two Google Fonts origins. [Renderer](evals/v1/render.py)

The LLM judge sees the brief, browser observations and four screenshots for each pair, with shuffled anonymous labels. Hierarchy, spacing, typography, color, accessibility and fidelity each count equally. The report gives the mean paired difference, wins, ties and losses, a paired bootstrap interval, and the status of every cell. Accessibility scores describe what the available browser evidence can show. [Rubric](evals/v1/rubric.md) · [Judge](evals/v1/judge.py)

## Candidate decisions

| Candidate | Observed change | Status |
| --- | --- | --- |
| Form directions, `d5a3278` | The six form briefs went from 0/6 to 6/6 correct surface routes. The unchanged 36-brief diagnostic returned `object-hero` on 26/36, down from 32/36. Source tests passed 341/341. | Separate branch. Route calibration occurred after the first source probe. Independent visual results remain pending. [Source results](evidence/benchmark-v1/form-candidate-source.json) |
| Broadcast and service booking, `384d61d` | Two matched blind comparisons averaged 89.6 for the frozen v2 and 97.9 for the candidate. Radio scored 87.5 → 95.8. Bike booking scored 91.7 → 100.0. Four other landing briefs kept their original direction in the six-call replay. | Integrated at `9756a34`. All eight browser keyboard checks passed across both arms and widths. All six integrated direction replies matched the candidate, the 17-tool stdio smoke passed, and the source suite passed 338 tests. [Paired visual scores](evidence/benchmark-v1/specific-landing-visual.json) · [Browser actions](evidence/benchmark-v1/specific-landing-actions.json) · [Integrated stdio and tests](evidence/benchmark-v1/specific-landing-integration.json) |
| Mobile product hero, `9de7829` | On the matched ceramics brief, the candidate scored 95.8 against 87.5 for frozen v2. The critique identified tighter mobile grouping of the artwork, price, shipping time and purchase action. | Integrated at `5cc8074`. Both builds added one bowl, opened the bag and restored keyboard focus at both widths. The integrated source passed 338 tests and 17 stdio calls. The fresh coffee and train comparison is separate. [Visual and interaction receipts](evidence/benchmark-v1/product-hero-visual.json) |
| Portable package and doctor, `7caf890` | Package resources and a checksum-pinned legacy cache support Python 3.10–3.13. The 36 directions, 21 reactions and one source check had identical normalized replies on Python 3.12. | Integrated on the rebuild branch. All eight macOS 15 jobs passed with pipx, uv, `doctor`, and all 17 tools on Intel and arm64. macOS 13 and fresh Tart remain open. [Output parity](evidence/benchmark-v1/portable-parity.json) · [Final hosted jobs](https://github.com/chrismicah/design-mcp/actions/runs/44987155008) |

The final portability candidate also returned the same structured results as the frozen baseline for all 17 stdio smoke calls at each of two fixed Python hash seeds. The comparison and library tools vary their ordering with the seed in both versions. The matched test verifies the package change independently of that existing behavior. [Stdio parity receipt](evidence/benchmark-v1/portable-stdio-parity.json)

Apply the same prompts, asset policy and scoring to each candidate. Preserve failed runs and report coverage alongside quality and tokens.

Both specific-landing v2 controls were scored again alongside the candidate. Their rescored values differ from the earlier v2-versus-plain ballots. Use the scores within each pair for candidate decisions. Both comparisons used the original benchmark rubric for captured states.

## Compact vision experiment

Across two briefs, the compact packets used 48,695 input tokens versus 51,112 with full screenshots, a 4.7% reduction. The theatre comparison kept both scores. The ceramics comparison moved from a tie to a 4.2-point lead for the plain generator. The compact run changed image size and supplied region measurements, so this comparison cannot isolate either change. Keep the full-size packets for the benchmark and measure region detection, decision agreement, and token savings on unseen examples before using compact packets by default. [Blind ballots and usage](evidence/benchmark-v1/compact-vision.json)

## Competitor search coverage

All four pinned credential-free tools were installed in CI and called on all 36 original briefs. Three returned matches for every brief and Design Library's keyword mode returned none when given the full brief. The earlier keyword preflight yielded a settings result, so the generator comparison allows the agent to choose search terms. On the frozen ceramics brief, Design MCP scored 91.7 against 87.5 for hosted Inspo and tied Offline Designer at 91.7. Both comparisons cover one brief. [Retrieval and visual scoreboard](teardown/COMPETITORS.md#retrieval-with-the-full-benchmark-briefs) · [Inspo receipt](evidence/benchmark-v1/hosted-inspo-ceramics.json) · [Offline Designer receipt](evidence/benchmark-v1/offline-designer-ceramics.json)
