# Design MCP benchmark

The baseline pins Design MCP at `fd6035d8732d177b811f81a0f5863e99134a85ca`. The control runs the same generator with no MCP. The 36 briefs include six each for landing pages, dashboards, forms, mobile web, settings and empty states. The historical `master` revision and the earlier six-brief study are separate comparisons. [Tasks](evals/v1/tasks.json) · [Earlier study](evidence/rebuild/comparison/README.md)

## Baseline scoreboard

| Configuration | Judged pairs | Score / 100 |
| --- | ---: | ---: |
| Same generator without MCP | 2 / 36 | 91.7 |
| Same generator with Design MCP v2 | 2 / 36 | 95.8 |

The first two pairs yielded a **+4.2-point** average difference, with one win and one tie. Rehearsal rooms scored 91.7 → 100.0. Ceramics scored 91.7 → 91.7. This is an early baseline for the existing revision. [Paired ballots and captures](evidence/benchmark-v1/first-pairs.json)

The first dashboard attempt called `direct` successfully and reached the client’s 240-second timeout before returning HTML. There was no completed-turn token receipt. The paired run uses a 900-second allowance for both arms and retains the first attempt separately. Playwriter MCP `0.12.0` rendered the isolated Chrome 157 control at both widths. The injected failure control detected narrow viewport overflow and the expected JavaScript error. [Tracked receipts](evidence/benchmark-v1/preflight.json)

The shared Mac’s memory-pressure gate held subsequent local rendering. GitHub’s standard macOS runner captured both initial pairs with Playwriter 0.12.0 and Chrome for Testing 158.0.8127.36 at the two preset widths. Each capture had no horizontal overflow or page errors. The next pairs will use the same pinned hosted renderer. [Capture run](https://github.com/chrismicah/design-mcp/actions/runs/44984687051)

| Brief | Configuration | Input tokens | Cached input | Output tokens | Seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| Rehearsal room board | Plain generator | 40,614 | 17,280 | 18,898 | 382.69 |
| Rehearsal room board | Design MCP v2 | 63,611 | 40,704 | 16,255 | 332.83 |
| Ceramics landing page | Plain generator | 40,367 | 19,840 | 22,702 | 459.69 |
| Ceramics landing page | Design MCP v2 | 62,609 | 40,192 | 22,183 | 450.60 |

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
| Portable package and doctor | A draft adds package-resource loading, a checksum-pinned legacy cache and Python 3.10–3.13 dependency resolution. The 36 direct results, 21 reactions and one source check were byte-identical after normalization to sorted JSON on Python 3.12. | All eight macOS 15 jobs passed with pipx, uv, `doctor`, and all 17 tools on Intel and arm64 across Python 3.10–3.13. Fresh Tart and integration review remain open. [Output parity](evidence/benchmark-v1/portable-parity.json) · [Hosted jobs](https://github.com/chrismicah/design-mcp/actions/runs/44986507623) |

Apply the same prompts, asset policy and scoring to each candidate. Preserve failed runs and report coverage alongside quality and tokens.
