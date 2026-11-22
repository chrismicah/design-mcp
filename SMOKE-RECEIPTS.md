# Design MCP live smoke

## Fresh-package benchmark smoke, November 21

Codex CLI 0.170.0 called `direct` through a fresh pipx install of `fd6035d` and returned an independent rehearsal room board. Playwriter MCP in isolated Chrome clicked the filter at 1440 px and used Tab and Enter at 390 px. “Delayed only” left Studio B visible, hid Hall A and announced one of two rooms. “All rooms” restored both. [Interaction receipt](evidence/benchmark-v1/preflight.json) · [390 px filtered screenshot](.context/factory/benchmark-v1/computer-smoke/interaction-v2/delayed-390.png)

GPT Computer Use opened a separate Chrome window. Its clipboard operation conflicted before navigation, and the isolated browser connector was unavailable. The fresh-package smoke therefore has Playwriter interaction evidence. Visual acceptance and blinded comparison remain open. [Benchmark](EVALS.md)

On November 22, GPT Computer Use could enumerate native apps and the browser access host still reported unavailable. Chrome was closed during that check. The native smoke was deferred. Separately, hosted Playwriter verified invalid submission, keyboard entry, local confirmation, and editing on the two exact maintenance benchmark pages at both widths. [Maintenance replay](evidence/benchmark-v1/maintenance-actions.json)

## November 20 source-checkout smoke

The owner rejected the original visual output after the functional pass. The theatre follow-up has its own direction and browser receipt. [Theatre call sheet revision](evidence/rebuild/live-smoke/theatre-revision.md)

**Functional pass for one generated app.** On November 20, 2026, Codex CLI called the candidate MCP and generated an interactive theatre turnaround board from a short brief. GPT Computer Use drove it in Chrome at desktop width and at a measured 390 CSS pixels. This run covers the source checkout and one brief. The fresh-package install, six-brief comparison and post-cull smoke remain pending.

## Candidate and client

- Candidate `52540b5a46d6ac8639d1f7aeb0f5f4931faa0a1a` on `design-mcp/f-held-out-fixes`. The client ran that checkout's CLI module over stdio in `v2` mode with Python 3.13.3 and FastMCP 3.1.0 from an existing dependency environment.
- The initial Codex call stopped at an approval request. The three v2 tools compute with bundled data and do not write files or call external services. The fix advertises this via MCP annotations and the README documents Codex's `writes` approval mode. The successful rerun used those settings through a one-run override.
- Claude Code discovered `direct`, `react`, and `check`. Its model request failed authentication with the existing session. The model-driven pass used the signed-in Codex CLI 0.170.0 with GPT-6.2 Sol.
- The successful client run passed `surface=dashboard` explicitly. It returned `exception-first` after one `direct` call and zero clarifications. The interval from log creation to the completed turn was approximately 56 seconds, including client startup and HTML generation. This was the README brief with an added filter task, so it leaves automatic surface inference and held-out generalization unverified. [Prompt](evidence/rebuild/live-smoke/prompt.txt) · [Client input, response, usage and hashes](evidence/rebuild/live-smoke/client-receipt.json)

## GPT Computer Use

| Scenario | Input | Verified live result |
| --- | --- | --- |
| Desktop initial state | Open generated HTML in a dedicated Chrome window | Studio B shows six minutes late. Hall A shows ready. |
| Desktop filter | Tab to Focus Studio B, press Enter | Studio B remains, Hall A leaves the list, Delayed is pressed, and the live status says one delayed room. A visible focus ring follows focus to Delayed. |
| Desktop restore | Click All rooms | Both rows return and All rooms is pressed. |
| 390 px initial state | Open the unchanged HTML in a 390 × 844 CSS pixel frame | The frame reports a 390 px document width and 390 px scroll width. IBM Plex Sans and IBM Plex Sans Condensed loaded. |
| 390 px filter | Click Focus Studio B | Only Studio B remains, the delayed status appears, and focus moves to Delayed. |
| 390 px restore | Shift+Tab to All rooms, then Enter | The status says “Showing both rooms.” Both original statuses return. |

The macOS Chrome window was used for input. The narrow test used a frame in the same Chrome window. Screenshots corroborate the browser accessibility observations. The earlier Linehaul challenge fixture also filtered to LS-057 and restored all five loads at both widths.

Local proof lives under `.context/rebuild/live/`: [generated HTML](.context/rebuild/live/site/stage.html), [desktop after filtering](.context/rebuild/live/stage-desktop-filtered.png), [390 px after filtering](.context/rebuild/live/stage-390-filtered.png), and [390 px after restoring both rooms](.context/rebuild/live/theatre-mobile.png). The checkout contains hashes in the client receipt. These local screenshots stay in the workspace.

## Design findings

The focal strip makes the delay, room and action easy to find. The grayscale squint check preserves the hierarchy, but the shape still reads as a conventional status dashboard. Both layouts repeat Hall A in the ready rail and the list. The mobile rail appears ahead of the queue visually while following it in the document order. The generated page has no transition for the filter or status change, so signature motion was absent.

Fable 5.2 independently reviewed the candidate annotations, the client receipt, and the four-image comparison. It verified that the hints describe the current tools, accepted the narrow functional result, and judged the first draft below the award benchmark. It identified the large empty desktop area after filtering and the generic shape of the exception strip. Its assessment used the desktop comparison sheet, with the model and source disclosed.

The static tell sweep returned zero recognized findings. The source checker does not measure the repetition, the reading-order discrepancy or the absence of a meaningful transition. A non-blind side-by-side compared use of focal hierarchy and subject matter with Studio D, A24 and Agrumea. The theatre board uses its exception strip well for the operational task. The award stills use subject-specific composition more strongly. The awards serve as craft references for this smoke. A paired baseline comparison for the same task remains pending. [Local grayscale blur](.context/rebuild/live/theatre-squint.png) · [Local side-by-side](.context/rebuild/live/theatre-awwwards-comparison.jpg) · [Award sources](evidence/research/UI-SOURCES.md)

## Regression checks and next gate

All 307 tests passed. Stdio smoke exercised all 17 tools in `both`, all 14 in `legacy`, and all three in `v2`. `react` with “calmer” returned a bounded revision for this direction over stdio. A live revised render remains pending. [Test log](evidence/rebuild/live-smoke/pytest.log) · [Both](evidence/rebuild/live-smoke/stdio-both-annotations.json) · [Legacy](evidence/rebuild/live-smoke/stdio-legacy-annotations.json) · [V2](evidence/rebuild/live-smoke/stdio-v2-annotations.json)

The shared Mac reported 30.31 GiB free and memory pressure level 2. Its resource gate declined the batch browser captures and fresh package build. The six-brief comparison, corpus cull and expansion, adversarial rerun and fresh-clone smoke are open. Conductor declined a new Astra session at the same pressure level.
