# Design MCP live smoke

## Direct Git install on both architectures, November 22

Both README commands installed `f17bd6f` directly from Git on clean macOS 15 runners. All eight Intel and Apple Silicon jobs passed on Python 3.10–3.13. The archived logs show 16 installs, 16 doctor checks, and 32 smoke runs across the default and compatibility surfaces. Each install verified the exact Git commit in its package metadata. Fresh Ventura remains open. [Job and source receipts](evidence/benchmark-v1/direct-git-install-f17bd6f.json) · [Earlier pin](evidence/benchmark-v1/direct-git-install-2fcd312.json)

## Reference Mac GPT Computer Use, November 22

A fresh uv install of the verified `f17bd6f` Git archive passed `doctor` and the three default stdio calls on Apple Silicon macOS 26.5.2. GPT Computer Use controlled installed Chrome 157 through its native accessibility tree while the browser bridge was unavailable. It loaded the five verified extension files in a disposable profile, opened the real toolbar, confirmed that a missing native host returned focus to Scan, then installed the host inside that profile. [Install, layout and interaction receipts](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

On the seeded fixture, the scan found text at **2.6:1** for a **4.5:1** requirement and reported **337 ms** for the one scan. The tool selected After by keyboard and reopened the same saved file in a fresh tab on Before. The archived preview and metadata stayed inside the profile. The embedded capture’s field mask matched RGB `138, 143, 152` in its interior, and the seeded field value was absent from the saved HTML and JSON. The 30-trial reference-Mac timing test remains open. [Action log and screenshot hashes](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

## Reference Mac SwiftUI, November 22

The hosted macOS job built a SwiftUI fixture targeting macOS 13, tested it against `f17bd6f`, and archived the same executable. On macOS 26.5.2, GPT Computer Use activated Reveal and verified that the new control appeared in the same window, in both Accessibility and the screenshot. The installed CLI replayed the hashed XCUITest geometry from the hosted run and confirmed five controls before and six after. It also replayed the hosted Electron window exports and confirmed the cleared occlusion and retained clipping finding. The local Electron walkthrough remains open. [Exact fixture build and capture](https://github.com/chrismicah/design-mcp/actions/runs/45028701101) · [Local action and CLI replay evidence](evidence/benchmark-v1/reference-mac-desktop-f17bd6f.json)

## Reference Mac clean install, November 22

Pipx 1.7.1 installed the exact combined candidate from a checked Git archive into a new workspace-local environment on Apple Silicon macOS 26.5.2 with Python 3.13.3. From an empty run directory, `doctor` passed and the installed server returned all three default tool replies and all 17 compatibility replies over stdio. The compatibility run created the verified 10,092,399-byte legacy cache. The installed package included the Chrome extension manifest. A fresh Codex CLI session using the documented stdio configuration called `direct`, `react`, and `check` against that executable. It received the service-work-order direction for the bike shop and applied the “calmer” reaction. The native browser run remains open. [Install and model trace receipts](evidence/benchmark-v1/reference-mac-install.json)

A separate offline uv install from the verified `2fcd312` archive passed `doctor` and all three default stdio tools on the reference Mac. The five installed extension files matched the archive. This gives the native walkthrough an exact package and local fixture. The browser access host was still unavailable during the staged check. [Exact local install receipt](evidence/benchmark-v1/reference-mac-install-2fcd312.json)

## Installed Chrome extension on hosted macOS, November 22

Chrome for Testing 158 opened the real toolbar by pointer on macOS 15.8.2 arm64 using the installed `f17bd6f` package. All three fresh profiles saved into their own histories, selected After by keyboard, and reopened the same preview on Before. The first archived preview passed the pixel mask and seeded-value checks again after download. The three trials establish the interaction and storage behavior. Reference-Mac latency remains open. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/45027525374) · [Exact profile and capture receipts](evidence/benchmark-v1/chrome-profile-review-isolation.json)

Chrome for Testing 158 loaded the extension from an install of `2fcd312` on macOS 15.8.2 arm64. The OS shortcut opened the toolbar popup in a fresh profile. Browser-targeted keyboard input activated Scan, exercised missing-host recovery, and opened the saved preview. The single scan took **141 ms** and flagged the seeded text at 2.6:1 against a 4.5:1 minimum. The keyboard selected After and moved focus to it. A new tab reopened the same file on Before. The downloaded evidence contained one masked field whose visible interior matched the mask color, and no seeded field value. The popup closed when opening the preview, so the test verified the new tab independently of the key acknowledgement. Reference-Mac latency and the GPT Computer Use walkthrough remain open. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/45012207196) · [Audited artifact hashes](evidence/benchmark-v1/chrome-extension-mac-2fcd312.json)

## Combined review branch, November 22

Four fresh-install hosted checks passed on `design-mcp/review-integration` at `2fcd312`. The public address form produced two Playwriter captures with nine masked fields and zero local findings. The Linux Chrome popup recovered from a missing host, masked the test field, and selected After by keyboard. Its single scan reported 96 ms. On hosted macOS 15 arm64, Electron cleared the seeded occlusion and retained the clipping finding. The SwiftUI fixture exposed a sixth control after Reveal. [Exact run links and artifact hashes](evidence/benchmark-v1/review-integration-2fcd312.json) · [Earlier combined receipt](evidence/benchmark-v1/review-integration.json)

In 30 further Linux trials, each keyboard toolbar activation opened a fresh popup document and each scan launched a one-request native host. The browser and fixture tab stayed warm. The p95 time through two animation frames after the control became visible was **299 ms** from the toolbar shortcut and **118 ms** from Scan to the finding. The popup exceeded the 250 ms target on this runner. The scan cleared its 1 s target. The timing includes keyboard injection and browser observation. [Trial timings and run](evidence/benchmark-v1/chrome-popup-latency-linux.json)

Two 30-trial diagnostic runs reduced injected key dispatch from 45 ms to 7 ms at the median. Both runs measured 299 ms p95 from shortcut to observed control. The popup document started around 249 ms after the shortcut in both runs. Most of the observed wait occurs before the popup's code can run. The reference Mac pointer measurement is still open. [Timing breakdown and raw receipt hashes](evidence/benchmark-v1/chrome-popup-latency-linux.json)

Two hosted macOS repeats each recorded one popup activation and scan before the next toolbar shortcut timed out. The run configured to dismiss the popup with Escape timed out before its first measured popup, so it never reached Escape. The two individual timings leave the warm-profile macOS p95 unverified. [Run receipts and hashes](evidence/benchmark-v1/chrome-popup-latency-mac-diagnostics.json)

A separate hosted macOS 15 test completed **30 of 30** keyboard trials by using an empty profile and a new Chrome process for each first activation. After the fixture loaded, p95 was **720 ms to the enabled popup** and **317 ms from Scan to the finding**. The popup missed 250 ms and the scan cleared 1 second. Median elapsed time to observe the popup target was 327 ms, including keyboard dispatch. The final mask archive failed because the first saved preview had aged out of the 20-review history. All 30 previews opened and reopened during their individual trials. [Audited timings](evidence/benchmark-v1/chrome-first-activation-mac.json)

The archive fix preserved the first saved preview on the next run. **25 of 30** trials completed. Trials 3, 8, 12, 16 and 22 timed out at the toolbar shortcut. The run withheld p95 and skipped the hosted mask step. Replaying that verifier locally on a copy confirmed the archived preview's mask pixels, screenshot hash and absence of the seeded field value from the preview and evidence. [Repeat run and mask replay](evidence/benchmark-v1/chrome-first-activation-mac.json)

The hosted pointer diagnostic seeded only the installed extension's pin in each fresh profile. The first run rejected Chrome's accessible toolbar label. Matching its first line made two of the next three runs complete the scan and reopen the saved preview. The enabled popup appeared in **1,018 ms** and **468 ms** from native mouse down. One attempt refused to click because Chrome reported two windows. The archived preview passed redaction. [Pointer trial receipts](evidence/benchmark-v1/chrome-pointer-activation-mac.json)

After checking the focused window against the fixture title, **30 of 30** pointer activations, scans and preview reopens completed. Five attempts completed with multiple Chrome windows present. Hosted p95 was **516 ms** from mouse down to the enabled popup and **233 ms** from Scan to the finding. Eleven opens met the 250 ms target, and every scan met 1 second. The p95 time to observe Chrome's popup target was 371 ms, including target observation overhead. The saved preview passed redaction. Reference-Mac timing and the GPT Computer Use sequence remain open. [CI run](https://github.com/chrismicah/design-mcp/actions/runs/45024065791) · [Per-trial receipts](evidence/benchmark-v1/chrome-pointer-activation-mac.json)

## Fresh-package benchmark smoke, November 21

Codex CLI 0.170.0 called `direct` through a fresh pipx install of `fd6035d` and returned an independent rehearsal room board. Playwriter MCP in isolated Chrome clicked the filter at 1440 px and used Tab and Enter at 390 px. “Delayed only” left Studio B visible, hid Hall A and announced one of two rooms. “All rooms” restored both. [Interaction receipt](evidence/benchmark-v1/preflight.json) · [390 px filtered screenshot](.context/factory/benchmark-v1/computer-smoke/interaction-v2/delayed-390.png)

GPT Computer Use opened a separate Chrome window. Its clipboard operation conflicted before navigation, and the isolated browser connector was unavailable. The fresh-package smoke therefore has Playwriter interaction evidence. Visual acceptance and blinded comparison remain open. [Benchmark](EVALS.md)

On November 22, GPT Computer Use could enumerate native apps and the browser access host still reported unavailable. Chrome was closed during that check. The native smoke was deferred. Separately, hosted Playwriter verified invalid submission, keyboard entry, local confirmation, and editing on the two exact maintenance benchmark pages at both widths. [Maintenance replay](evidence/benchmark-v1/maintenance-actions.json)

A later desktop preflight ran after the previous QA owner released the Mac. The workspace stager recorded both displays and flagged Notes and TextEdit windows. The browser access host reported unavailable with Chrome closed, including on the 09:10 UTC recheck. Both checks preserved those windows and sent no input. Native extension activation and reopening the preview remain unverified.

At the 12:06 UTC handoff check, the ML QA owner had released its slot. The workspace inventory showed Swipe Clean frontmost, a TextEdit dialog, and two displays. GPT Computer Use enumerated apps and again reported that the browser access host was unavailable. The staging check saved both displays locally and sent no input.

At the subsequent read-only check, GPT Computer Use could still enumerate apps, with Chrome absent from the running inventory and the browser access host unavailable. No desktop input was sent.

## Hosted Chrome extension smoke, November 22

A fresh Linux Chrome install of `f17bd6f` went through the missing-host recovery and saved the preview under the disposable Chrome profile. Keyboard input selected and focused After. The saved capture's mask pixels matched the expected color, and the seeded field value was absent. A focused regression separately checked the review-history retention boundary. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/45026500852) · [Receipt and hashes](evidence/benchmark-v1/chrome-profile-review-isolation.json)

A fresh package install on hosted Linux opened the real toolbar popup by keyboard on a synthetic shuttle dispatch board. Scan started focused. With the host missing, the popup gave the install command and returned focus to Scan. After installing the host into the isolated Chrome user data directory, Enter scanned eight regions, opened a saved preview, and the Right Arrow switched to After. The archived capture masked the seeded field and the private value was absent from the saved HTML and JSON. The popup reported 87 ms on this run. The hosted macOS runs described above add fresh-profile evidence. Reference-Mac pointer timing, GPT Computer Use smoke and blind visual scoring remain open. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/44994211431) · [Receipt and hashes](evidence/benchmark-v1/vision-extension-proof.json)

## Hosted Electron window smoke, November 22

A fresh package install reviewed an owned Electron 43.4.0 fixture on Linux. The first capture identified a covered button and a clipped button. Tab followed by Enter revealed the covered button, and a second capture cleared that finding while retaining the clipping finding. The export excluded the seeded input value, refused an unsupported source, and kept the original file intact. The separate Swift exporter type-checked with warnings as errors for the macOS 13 arm64 target. Desktop visual review remains open. [Electron run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/44994843695) · [Receipts and hashes](evidence/benchmark-v1/desktop-app-proof.json)

## Hosted Electron window on macOS, November 22

The fresh package and Electron 43.4.0 repeated the window test on macOS 15.8.2 arm64. Tab and Return in the focused window made the covered control hittable and cleared that specific finding. The clipped control stayed flagged. The geometry exports omitted the seeded input value and the original export survived the overwrite attempt. This uses Electron’s input API in the owned app. [Mac run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/44995434475) · [Receipt and hashes](evidence/benchmark-v1/electron-mac-proof.json)

## Hosted native SwiftUI smoke, November 22

A macOS 15.8.2 arm64 runner built and opened an owned SwiftUI app. XCUITest clicked the native Reveal control and verified that another native control became visible and hittable. The installed Design MCP CLI read the paired Accessibility exports and counted five controls before and six after. Window dimensions matched, and both screenshots came from that window. The test refused a missing window and preserved the earlier export on a second write attempt. The secure field’s seeded value was absent from both geometry exports. This exercise covers one app and the geometry reviewer. Desktop visual critique, macOS 13 runtime, and the GPT Computer Use release smoke remain open. [Native run and captures](https://github.com/chrismicah/design-mcp/actions/runs/44995163235) · [Receipt and hashes](evidence/benchmark-v1/swift-review-proof.json)

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
