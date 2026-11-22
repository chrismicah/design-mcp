# Website review with browser evidence and frontier vision

## Calibration

The renderer captured the same two matched briefs with Chrome for Testing and Playwriter MCP. The full-input judge saw four original screenshots with an accessibility excerpt. The compact judge saw the original 390 px screens, two 720 px desktop images, and the visible regions' CSS boxes, labels, active type, ink, fills and pressed states. The same frontier model and scored rubric ran in separate blind sessions. [Capture run](https://github.com/chrismicah/design-mcp/actions/runs/44985648610) · [Both ballots and token receipts](../evidence/benchmark-v1/compact-vision.json)

| Judge input | Tokens in | Tokens out | Rehearsal rooms | Ceramics |
| --- | ---: | ---: | --- | --- |
| Full | 51,112 | 7,755 | MCP win | Tie |
| Compact | 48,695 | 7,256 | MCP win | Plain generator win |

Compact input used 4.7% fewer input tokens. One of two preferences changed. The two independent readings cannot isolate image resolution, extra geometry, or model variation. Keep full-resolution evidence for the release critic. Use compact browser observations to locate and describe issues before sending images to a frontier model.

At 390 px, the collected theatre evidence located “Delayed only” at `[138, 239, 118, 44]` in CSS pixels, identified its active type and unpressed state, and located the two-room status. A separate browser action changed the visible list, pressed state and status and then restored them. Geometry can establish what fit and what moved. A design judgment can assess whether the exception and next action are legible at a glance. [Browser interaction receipt](../evidence/benchmark-v1/preflight.json)

On the live U.S. Web Design System address-form page, the original desktop collector spent all twelve slots on page chrome while the form was visible in the screenshot. Reserving slots for the main landmark recovered the heading and street-address label at both 1440 and 390 CSS pixels with only eight regions per view. The two captures used the same pinned Playwriter and Chrome versions. [Region and screenshot hashes](../evidence/benchmark-v1/live-source-regions.json) · [Before](https://github.com/chrismicah/design-mcp/actions/runs/44987189080) · [After](https://github.com/chrismicah/design-mcp/actions/runs/44987457905)

The installed `design-mcp review` prototype captured that reference at both widths and saved a local preview. It reported nine masked fields across two views. All five sampled desktop field centers had the expected mask color in the original preview PNG. The first collector omitted the visible Street address field from both context packets. The revised collector recovered the field at 1440 and 390 px with eight regions per view and the same mask counts. The follow-up measured 656 ms total for the two captures, 0.1 ms for local checks, and 3.6 ms to build and save the preview after normalization. This is one hosted run. Popup timing, seeded field privacy, and blind live critique remain open. [Installed runs and receipts](../evidence/benchmark-v1/vision-url-proof.json)

## Recommended review flow

Astra recommended starting with a pasted public URL in an isolated, cookie-free browser. Add Chrome `activeTab` as a shortcut into the same review engine. A review shows the first useful weakness with its page location, then offers a separate local preview. The extension's primary action is Scan. Measure 30 cold opens and 30 cold scans, with p95 targets of 250 ms to a painted, enabled Scan control and 1 second from Scan to the first painted local finding. Time frontier review separately. [Rollout plan](../PLAN.md#11-rollout-after-slice-g) · [Chrome active tab](https://developer.chrome.com/docs/extensions/develop/concepts/activeTab) · [Native messaging](https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging)

1. **Collect observable facts locally.** Use one frame ID and up to eight named regions per viewport. Keep rounded boxes, computed typography and color, accessibility names, reading order and an observed interaction delta when useful. Check for measured overflow, an overlapping layer at the main action, and contrast failures on known flat fills. Leave complex fills and missing fields for review. Mask editable fields and private content before storage or model submission. [Contrast criterion](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
2. **Call frontier vision for judgment.** Supply the visitor's task and a compact overview plus the facts needed to explain the result. Add up to two native-resolution crops when text is too small, imagery loses material detail, or a layout relationship remains unclear. The criticism should identify a region, a visible defect, and one change with an observable outcome.
3. **Keep the release decision independent.** Separate candidate generation from anonymous criticism. Check actual keyboard behavior, page geometry and privacy before sending full-size desktop and mobile views to the release critic. Require at least 9.5/10 on the release screen set. Keep original task facts and actions intact. Use native GPT Computer Use to verify paste, first feedback, preview and export in a real user flow.

First replay the theatre case with identical prompts and region facts in both arms. Require the compact packet to preserve the diagnosis and task outcome while reducing input tokens by at least 40%, including any additional crops. If it clears that check, calibrate on unseen pages. Measure regional defect precision and recall, agreement with full-size captures with the same browser evidence, real interaction outcomes, input tokens and total latency including escalations. The main savings hypothesis is fewer frontier calls after deterministic checks.

## Concept updates

Record each new concept's source, rights, applicable task, visual principle, and counterexample. Compare it with existing entries for the same task and review a generated result on held-out briefs before promoting it. Import the next catalog version separately from the installed runtime. Track direction concentration so a new library cannot quietly reproduce the 32/36 default-route collapse. [Default routing probe](../EVALS.md#direction-coverage) · [Adoption experiments](ADOPTION.md)

## When to spend another evaluation call

Anthropic's long-running app experiments separated planner, generator, and evaluator. The design evaluator emphasized coherence and originality, tested the live page, and cited concrete failures. Some middle iterations were stronger than the final one. Its full game-maker harness took six hours and reported $200 in token costs, versus 20 minutes and $9 for the solo run. Its later experiment removed per-sprint evaluation for a more capable builder and used targeted QA passes. These are observations from that harness. [Anthropic engineering report](https://www.anthropic.com/engineering/harness-design-long-running-apps)

For Design MCP, agree on the real browser interaction and visual criteria before each meaningful revision. Let deterministic tests handle mechanical changes. Use a fresh blind critic for a candidate or material visual change, weight coherence and originality highest, and keep the best verified iteration. Carry region, weakness, proposed repair, and expected measurable change into the next build. Use a fresh context with those artifacts when a long session starts losing constraints. [Release rubric and gate](../evals/vision/rubric.md)
