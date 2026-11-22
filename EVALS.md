# Design MCP benchmark

The baseline pins Design MCP at `fd6035d8732d177b811f81a0f5863e99134a85ca`. The control runs the same generator with no MCP. The 36 briefs include six each for landing pages, dashboards, forms, mobile web, settings and empty states. The historical `master` revision and the earlier six-brief study are separate comparisons. [Tasks](evals/v1/tasks.json) · [Earlier study](evidence/rebuild/comparison/README.md)

## Baseline scoreboard

| Configuration | Judged pairs | Score / 100 |
| --- | ---: | ---: |
| Same generator without MCP | 0 / 36 | Pending |
| Same generator with Design MCP v2 | 0 / 36 | Pending |

The first dashboard attempt called `direct` successfully and reached the client’s 240-second timeout before returning HTML. There was no completed-turn token receipt. The paired run uses a 900-second allowance for both arms and retains the first attempt separately. Playwriter MCP `0.12.0` rendered the isolated Chrome 157 control at both widths. The injected failure control detected narrow viewport overflow and the expected JavaScript error. [Tracked receipts](evidence/benchmark-v1/preflight.json)

The rehearsal-room and ceramics pairs returned HTML and token usage. The shared Mac’s memory-pressure gate held the next render. Generation continues on the existing subscription, and the scoring queue rechecks the gate.

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

Intel, macOS 13, and fresh Tart VM coverage remain open. [Tracked preflight receipt](evidence/benchmark-v1/preflight.json) · [pipx smoke](.context/factory/benchmark-v1/install/stdio-both.json) · [uv smoke](.context/factory/benchmark-v1/install/stdio-uv-3.13-both.json) · [3.10 install log](.context/factory/benchmark-v1/install/pipx-exact-3.10.log)

## How the score is calculated

The harness runs each brief in two fresh sessions with matching model, effort, prompt, tool restrictions and allowed assets. The treatment must complete a `direct` call. The control uses an empty MCP configuration. Each cell records the client version, exit status, prompt hash, tool calls, elapsed time and provider-reported token fields. The receipt keeps input, cached input and output counts as reported by the client. [Generator](evals/v1/generate.py)

Playwriter opens each page in isolated Chrome and saves the first viewport at 1440 × 900 and 390 × 844. The harness records active web fonts, horizontal overflow, language, page errors and an accessibility-tree excerpt. Page content is served only on loopback, with external requests limited to the two Google Fonts origins. [Renderer](evals/v1/render.py)

The LLM judge sees the brief, browser observations and four screenshots for each pair, with shuffled anonymous labels. Hierarchy, spacing, typography, color, accessibility and fidelity each count equally. The report gives the mean paired difference, wins, ties and losses, a paired bootstrap interval, and the status of every cell. Accessibility scores describe what the available browser evidence can show. [Rubric](evals/v1/rubric.md) · [Judge](evals/v1/judge.py)

## Candidate decisions

Candidate results go here after the baseline. Apply the same prompts, asset policy and scoring to each candidate. Preserve failed runs and report coverage alongside quality and tokens.
