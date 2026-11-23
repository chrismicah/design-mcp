# Design MCP live smoke

## Exact toolbar replay and hosted install matrix

All 13 checks passed on `d4c4d70`, including eight hosted macOS 15 architecture and Python cells. Two hosted Chrome runs pressed the actual toolbar action and reopened the masked saved result. Pasted URL took 1.858 and 1.619 seconds in those runs. The fresh SwiftUI capture showed five reviewed controls before Reveal and six after. The packaged Electron fixture removed the seeded occlusion and retained the clipping finding. Both original public URL PNGs matched the hosted receipt. The exact fresh Apple Silicon install also passed all six stdio configurations and recovered after a 404. The native BenQ replay and Intel Ventura test remain open. [Exact runs, local install and original frame hashes](evidence/benchmark-v1/release-ci-d4c4d70.json)

Two slower local captures spent 7.56 and 9.59 seconds in cleanup. A loopback regression on Python 3.13 reproduced the wait with a client that remained open after its initial proxy greeting. The experimental branch closes the owned proxy clients before waiting for the server. That regression passes, and median observed cleanup fell from 102.5 to 22.2 ms across ten fresh browser pairs. The full direct review was faster in eight pairs and nine PNG hashes matched. Mask counts and findings matched in all ten. The full-speed gate remains open and the patch remains isolated. [Paired timing and capture evidence](evidence/benchmark-v1/nov23-url-cleanup-pairs.json) · [Python server shutdown behavior](https://docs.python.org/3.13/library/asyncio-eventloop.html#asyncio.Server.wait_closed)

The independent reviewer reproduced another hang when a client stopped reading buffered output. The second patch aborts the disposed browser's client transports and passes both shutdown regressions. All ten replay pairs matched their PNGs, masks, and findings. Cleanup fell from 130.75 to 22.3 ms median. The full interval improved in eight pairs, with a 9.75% median paired reduction, so this still falls below the full-speed gate. The experiment passed 457 source tests and remains on its own branch. [Second replay](evidence/benchmark-v1/nov23-url-cleanup-pairs.json) · [Experiment branch](https://github.com/chrismicah/design-mcp/tree/design-mcp/url-cleanup-fix)

The release branch completed all 13 hosted checks again at `8b8415c`, including the eight install cells and fresh SwiftUI, Electron, Chrome toolbar, and public URL workflows. That run exercised the release runtime. [Exact checkpoint](https://github.com/chrismicah/design-mcp/commit/8b8415c27c1f6670130cd08bb4502f8aa0140782/checks)

## Creative verifier branch checkpoint

All 13 hosted checks passed on `bb0a124`, including 16 clean installs and 96 stdio sessions on macOS 15. The hosted Chrome replay exercised active-tab and pasted-URL review, five-field masking, and the saved keyboard preview. The pasted result opened in 2.49 seconds in this run. Fresh macOS SwiftUI captures showed five reviewed controls before Reveal and six after. In Electron, Reveal cleared the occlusion finding and the seeded clipping finding remained. The installed public URL review completed at 1440 and 390 CSS px. The package source matches the README install pin. [Exact jobs and captures](evidence/benchmark-v1/release-ci-bb0a124.json)

## Checkout cleanup and exact Chrome replay

`0978712149674ad7fd5738c53d4b7966ba163b43` is the README install pin. The migration staged 14 writable copies from a fresh Git archive, then wrote zero on repeat. The canonical legacy corpus retained its SHA-256. The root script exposed and called the historical surface from another working directory. The candidate passed **545 source tests and 120 subtests**. All eight hosted macOS 15 architecture/Python cells passed, with 16 fresh installs and 96 stdio sessions across the three surfaces with and without `review_page`. The exact hosted extension, public URL, SwiftUI, and Electron workflows passed. [Exact jobs and migration](evidence/benchmark-v1/release-ci-0978712.json)

On the reference Mac, GPT Computer Use verified both native Chrome flows with the updated extension files and a newly installed exact host. The active tab measured the seeded 2.64:1 contrast in 141 ms and saved a masked preview. Keyboard input opened the After view and the fixture changed from three routes to one and back to three. The pasted 404 restored focus and saved nothing. A retry created a 1440 × 900 capture with five masks in 6.37 seconds. Both saved previews reopened after reload. The current pasted-URL sample is slower than the earlier reference-Mac run. [Exact native Chrome receipt](evidence/benchmark-v1/release-native-chrome-0978712.json)

The cleanup pin also passed **eight clean installs, eight `doctor` calls, and 48 stdio runs** on Apple Silicon Ventura 13.7.4. The repeat used a disposable copy of the existing benchmark VM and new interpreter, tool, package, and evidence directories. The optional review calls checked its URL refusal path. The clone was stopped and deleted, and the scoped OCI cache remained empty. The earlier `a9e1211` run booted from a freshly pulled image. Intel Ventura remains unverified. [Exact Ventura transcript audit](evidence/benchmark-v1/ventura-tart-0978712.json)

A separate reference-Mac replay of the pinned installed `review_page` over stdio returned a 1440 × 900 PNG with five masked fields and a 390 × 844 PNG with four. The original PNG hashes matched the earlier public-form captures. Calls took 2.14 s and 0.79 s in that session, and the 404 returned a structured capture error. These are individual timings from an initial-view capture. [Installed PNG and error receipt](evidence/benchmark-v1/release-mcp-images-0978712.json)

## Portable CI smoke client

On `46e9913`, 11 of 12 hosted checks completed successfully. The Intel Python 3.11 job reached both installed entry points, then hit its 12-minute limit during the uv smoke commands. Its installer bootstrap spent five minutes compiling `cryptography` for the additional FastMCP client. The verifier now uses the client from each pipx and uv installation. A local replay with both existing environments passed all 12 stdio checks from an empty directory. The new hosted run will verify clean installs and timing. [Timed-out Intel job](https://github.com/chrismicah/design-mcp/actions/runs/45117704881/job/137504215007)

All 12 hosted checks then passed on `d27f386`, including all eight clean macOS 15 install cells. The preceding verifier commit `517145c` passed the previously timed-out Intel Python 3.11 cell in 4 minutes and 50 seconds. The pinned Ventura results remain a separate test. [Exact hosted jobs](evidence/benchmark-v1/release-ci-d27f386.json) · [First successful Intel rerun](https://github.com/chrismicah/design-mcp/actions/runs/45119455041/job/137509630188)

The hosted extension smoke on `5c2c058` reached the seeded fixture through CDP. Its first X11 lookup found no visible window with the fixture title and stopped before opening the extension. The harness now waits for that visible window with the existing bounded deadline. The local syntax check and all six popup capture consistency tests passed. [First hosted log](https://github.com/chrismicah/design-mcp/actions/runs/45123082505/job/137521109706)

## Active-tab capture candidate, November 22

`12e9524` passed all eight macOS 15 install jobs and the hosted Chrome, public URL, SwiftUI, and Electron workflows. The clean-install jobs used pipx and uv on Apple Silicon and Intel across Python 3.10–3.13. The hosted Chrome run verified active-tab masking, missing-host recovery, the Before and After keyboard switch, and opening the capture from a pasted URL. It saved the masked public form after **1.49 seconds** in that run. [Exact jobs and capture hashes](evidence/benchmark-v1/release-ci-12e9524.json)

The active-tab fix compares the mask geometry around capture. Six focused tests exercised stable capture, a moving or newly visible field, scroll, a changed tab, and successful retry. The changed cases returned focus to the scan action without handing off a capture. A fresh GPT Computer Use toolbar replay on macOS remains open for this commit. The Ventura and native walkthrough receipts below apply to `a9e1211`.

On the Apple Silicon reference Mac, a fresh uv install of `12e9524` completed all six stdio configurations from a separate empty working directory. The default, historical, and combined surfaces exercised **3, 14, and 17** successful fixture calls. Enabling review added a tested unsupported-address refusal to each. Over five fresh default processes, the median time through the first `direct` result was **555 ms**. The median of 15 warm `direct` calls was **1.65 ms**. The installed package measured **602 KB** and excluded the historical pattern snapshot and offline queues. The historical tools read the existing verified 10,092,399-byte cache. [Local stdio and package receipt](evidence/benchmark-v1/reference-mac-stdio-12e9524.json)

## Pinned release candidate, November 22

`a9e1211` passed **543 source tests and 120 subtests**, and **16 clean Git installs** across eight macOS 15 jobs. CI checked Python 3.10–3.13 on Apple Silicon and Intel, with pipx and uv in each job. Both installers ran all three stdio modes with and without `review_page`. The opt-in smoke verifies its structured refusal path. The installed Playwriter CLI reviewed the public address form at 1440 and 390 CSS px. [Exact workflows and artifacts](evidence/benchmark-v1/release-ci-a9e1211.json)

A fresh uv install from the exact Git archive passed `doctor` on the reference Mac. GPT Computer Use ran the byte-verified Chrome extension and its matching local host. **Review this page** found 2.6:1 contrast in 157 ms, saved a masked Retina capture, and opened the keyboard comparison. **Review URL** reported HTTP 404 and restored focus to the URL field without creating a review. A retry with the published address produced a 1440 × 900 capture in 2.48 seconds. It reopened with the five field masks intact. The timings are individual observations. [Walkthrough and original PNG hashes](evidence/benchmark-v1/release-native-chrome-a9e1211.json)

Hosted macOS fixtures produced fresh SwiftUI and Electron pixels and geometry. The SwiftUI control count changed from five to six after Reveal. The Electron action cleared occlusion while retaining the clipping finding. The exact hosted Chrome extension check ran on Linux. [Artifact hashes and linked jobs](evidence/benchmark-v1/release-ci-a9e1211.json)

The reference Mac also called the exact installed `review_page` over stdio at both widths. It returned original PNGs with five and four form-field masks. The desktop image matched the Chrome extension's saved capture. The live 404 returned a structured capture error. Each successful tool call took about 11.2 seconds in this run. Separately, an empty cache allowed offline use of the default tools. The legacy cache rejected same-size corruption and `doctor --repair` restored the pinned hash for offline use. [MCP images and timings](evidence/benchmark-v1/release-mcp-images-a9e1211.json) · [Cache proof](evidence/benchmark-v1/release-cache-a9e1211.json)

The installed reference-Mac catalog returned in 547 ms. The first ordinary-language direction took 65.7 ms, and two subsequent requests took 1.8 and 2.1 ms. The vague brief received one optional question with a default. The conflicting dashboard brief and routine maintenance form received none. Each direction accepted the one-word reaction `calmer` and returned a concrete change that preserved the primary task. These single timings cover stdio tool results. [Three-brief tool receipt](evidence/benchmark-v1/release-first-directions-a9e1211.json)

## Release candidate on both architectures

The work-order guidance release candidate at `a700f82` passed all 14 hosted checks. The matrix recorded 16 clean pipx and uv installs on macOS 15 and 96 stdio runs. The hosted Chrome fixture completed both review flows and verified the pasted-URL mask. New SwiftUI and Electron fixture captures and the installed public URL review passed. [Exact workflows and capture hashes](evidence/benchmark-v1/release-ci-a700f82.json)

All eight macOS 15 jobs passed on Intel and Apple Silicon with Python 3.10–3.13. The installers fetched GitHub's test merge `1ff95a2`, which has the same tree ID as `6e9a239`. Both installers passed `doctor`, exercised the default and combined surfaces, and verified the opt-in `review_page` error response. On the reference Mac, a fresh installation from `6e9a239` returned original 1440 × 900 and 390 × 844 PNGs of the public USWDS address form with five and four masked fields respectively. Playwriter separately exercised the theatre filter and restored the full list at both widths. In a disposable headless Chrome for Testing profile, submitting the URL returned a visual result in 4.14 seconds, preserved the masked preview after reload, and recovered from a missing reviewer host. [Mac install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45089158186) · [Installed browser and MCP receipt](evidence/benchmark-v1/release-initial-6e9a239.json)

## Direct Git install on both architectures, November 22

Both README commands installed `7bccfc1` directly from Git on clean macOS 15 runners. All eight Intel and Apple Silicon jobs passed on Python 3.10–3.13. The archived logs show 16 installs, 16 doctor checks, and 32 smoke runs across the default and compatibility surfaces. Each install verified the exact Git commit in its package metadata. Fresh Ventura remains open. [Current job and source receipts](evidence/benchmark-v1/direct-git-install-7bccfc1.json) · [Native walkthrough install pin](evidence/benchmark-v1/direct-git-install-f17bd6f.json)

## Reference Mac pasted URL, November 22

An offline uv install from the checksummed `7bccfc1` Git archive passed `doctor` and all three default stdio tools on the reference Apple Silicon Mac. The dedicated Chrome profile used byte-identical extension assets and a native host bound to that installed executable. GPT Computer Use entered the public USWDS address-form URL in the extension, opened it in a new tab, scanned it by keyboard and reloaded the same saved preview. Chrome showed the no-finding state and four masked fields. The popup reported 184 ms in that scan. The saved PNG passed a 35,000-pixel interior check of the Street address mask. [Install, actions and file hashes](evidence/benchmark-v1/reference-mac-pasted-url-7bccfc1.json)

The same installed CLI captured the public form through Playwriter at 1440 and 390 CSS px using a separate Chrome profile. It reported nine masks across both views. The saved preview displayed the desktop capture, whose Street address mask passed a 9,408-pixel interior check. [CLI capture and mask receipt](evidence/benchmark-v1/reference-mac-pasted-url-7bccfc1.json)

The `7bccfc1` install also replayed the original SwiftUI and Electron geometry exports. The SwiftUI fixture returned five controls before Reveal and six after. The Electron replay cleared the covered-control finding and retained the clipping finding. The replay verified the input hashes before and after execution. The live desktop interactions are recorded under `f17bd6f` below. [Installed replay](evidence/benchmark-v1/reference-mac-pasted-url-7bccfc1.json)

## Reference Mac GPT Computer Use, November 22

A fresh uv install of the verified `f17bd6f` Git archive passed `doctor` and the three default stdio calls on Apple Silicon macOS 26.5.2. GPT Computer Use controlled installed Chrome 157 through its native accessibility tree while the browser bridge was unavailable. It loaded the five verified extension files in a disposable profile, opened the real toolbar, confirmed that a missing native host returned focus to Scan, then installed the host inside that profile. [Install, layout and interaction receipts](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

On the seeded fixture, the scan found text at **2.6:1** for a **4.5:1** requirement and reported **337 ms** for the one scan. The tool selected After by keyboard and reopened the same saved file in a fresh tab on Before. The archived preview and metadata stayed inside the profile. The embedded capture’s field mask matched RGB `138, 143, 152` in its interior, and the seeded field value was absent from the saved HTML and JSON. [Action log and screenshot hashes](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

The subsequent native series completed all **30** pointer opens and keyboard scans in that running Chrome profile, closing the popup between trials. p95 was **136 ms** to the enabled Scan control and **100 ms** to the first finding. The measurement paired native event timestamps with the states exposed in Accessibility. The final visible screenshot showed the contrast issue, and the saved preview passed its field-mask and seeded-value checks. [Per-trial timings and capture hashes](evidence/benchmark-v1/chrome-reference-latency-f17bd6f.json)

## Reference Mac SwiftUI, November 22

The hosted macOS job built a SwiftUI fixture targeting macOS 13, tested it against `f17bd6f`, and archived the same executable. On macOS 26.5.2, GPT Computer Use activated Reveal and verified that the new control appeared in the same window, in both Accessibility and the screenshot. The installed CLI replayed the hashed XCUITest geometry from the hosted run and confirmed five controls before and six after. It also replayed the hosted Electron window exports and confirmed the cleared occlusion and retained clipping finding. [Exact fixture build and capture](https://github.com/chrismicah/design-mcp/actions/runs/45028701101) · [Local action and CLI replay evidence](evidence/benchmark-v1/reference-mac-desktop-f17bd6f.json)

## Reference Mac Electron, November 22

The owned Electron 43.4.0 app passed strict recursive signature and bundle identity checks on macOS 26.5.2 arm64. The first run stopped before input because the fixture expected 880 × 640 screenshot pixels on a Retina display. The harness now accepts the fixed 880 × 640 CSS viewport and validates the image at the display’s backing scale. Both new PNGs came from the original 1760 × 1280 capture.

GPT Computer Use pressed Tab to focus Reveal and Return to reveal the covered button. Accessibility, the screenshot, and the saved status agreed, and focus stayed on Reveal. The installed `f17bd6f` CLI read two fresh geometry exports, found four controls in each, and reported only the clipping finding after Reveal. The audit confirmed the covered region’s color changed from RGB `51, 51, 51` to `239, 239, 239`. The geometry exports omitted the seeded input value. [Local action, signature and capture receipt](evidence/benchmark-v1/reference-mac-electron-f17bd6f.json)

## Reference Mac clean install, November 22

Pipx 1.7.1 installed the exact combined candidate from a checked Git archive into a new workspace-local environment on Apple Silicon macOS 26.5.2 with Python 3.13.3. From an empty run directory, `doctor` passed and the installed server returned all three default tool replies and all 17 compatibility replies over stdio. The compatibility run created the verified 10,092,399-byte legacy cache. The installed package included the Chrome extension manifest. A fresh Codex CLI session using the documented stdio configuration called `direct`, `react`, and `check` against that executable. It received the service-work-order direction for the bike shop and applied the “calmer” reaction. The native browser run remains open. [Install and model trace receipts](evidence/benchmark-v1/reference-mac-install.json)

A separate offline uv install from the verified `2fcd312` archive passed `doctor` and all three default stdio tools on the reference Mac. The five installed extension files matched the archive. This gives the native walkthrough an exact package and local fixture. The browser access host was still unavailable during the staged check. [Exact local install receipt](evidence/benchmark-v1/reference-mac-install-2fcd312.json)

## Installed Chrome extension on hosted macOS, November 22

Chrome for Testing 158 opened the real toolbar by pointer on macOS 15.8.2 arm64 using the installed `f17bd6f` package. All three fresh profiles saved into their own histories, selected After by keyboard, and reopened the same preview on Before. The first archived preview passed the pixel mask and seeded-value checks again after download. The three trials establish the interaction and storage behavior. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/45027525374) · [Exact profile and capture receipts](evidence/benchmark-v1/chrome-profile-review-isolation.json)

Chrome for Testing 158 loaded the extension from an install of `2fcd312` on macOS 15.8.2 arm64. The OS shortcut opened the toolbar popup in a fresh profile. Browser-targeted keyboard input activated Scan, exercised missing-host recovery, and opened the saved preview. The single scan took **141 ms** and flagged the seeded text at 2.6:1 against a 4.5:1 minimum. The keyboard selected After and moved focus to it. A new tab reopened the same file on Before. The downloaded evidence contained one masked field whose visible interior matched the mask color, and no seeded field value. The popup closed when opening the preview, so the test verified the new tab independently of the key acknowledgement. The later `f17bd6f` walkthrough is recorded above. [Run and screenshots](https://github.com/chrismicah/design-mcp/actions/runs/45012207196) · [Audited artifact hashes](evidence/benchmark-v1/chrome-extension-mac-2fcd312.json)

## Combined review branch, November 22

Four fresh-install hosted checks passed on `design-mcp/review-integration` at `2fcd312`. The public address form produced two Playwriter captures with nine masked fields and zero local findings. The Linux Chrome popup recovered from a missing host, masked the test field, and selected After by keyboard. Its single scan reported 96 ms. On hosted macOS 15 arm64, Electron cleared the seeded occlusion and retained the clipping finding. The SwiftUI fixture exposed a sixth control after Reveal. [Exact run links and artifact hashes](evidence/benchmark-v1/review-integration-2fcd312.json) · [Earlier combined receipt](evidence/benchmark-v1/review-integration.json)

The installed `e1cd4eb` CLI found Playwriter 0.12.0 on PATH and used the session returned for its separate Chrome profile. The same public form produced matching PNG digests at 1440 × 900 and 390 × 844 with five and four masked fields. The original desktop PNG embedded in the saved preview matched its evidence hash. All 17,136 sampled interior pixels of Street address matched the mask color. The mobile capture contributed its geometry and image digest. [Hosted URL test](https://github.com/chrismicah/design-mcp/actions/runs/45032622125) · [Artifact audit](evidence/benchmark-v1/isolated-url-session-e1cd4eb.json)

The hosted `7bccfc1` install checked every proxied TCP destination. Headless Chrome sent an IPv4 loopback address and a test hostname resolving to loopback to the proxy. The owned private fixture received zero connections. The public address form matched the earlier desktop and mobile PNG digests, and the archived desktop mask passed the pixel audit. [Hosted URL test](https://github.com/chrismicah/design-mcp/actions/runs/45035151563) · [Artifact audit](evidence/benchmark-v1/browser-public-network-7bccfc1.json)

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

The new external-input mode waited for a keyboard event from a separate driver on the hosted X11 display. The default input path also passed on Linux and macOS. Replaying all three capture pairs through the installed `f17bd6f` CLI reproduced the clearing occlusion and persistent clipping. The downloaded screenshots corroborated the occlusion change, and the audit rejected a reused Before image. The first Linux attempt reached the capture and returned `UnknownVizError`. The retry requested software rendering for the virtual display. [Linux run](https://github.com/chrismicah/design-mcp/actions/runs/45029926558) · [Mac run](https://github.com/chrismicah/design-mcp/actions/runs/45029926480) · [Audit](evidence/benchmark-v1/electron-external-input-0c279d9.json)

The reference Mac downloaded the official arm64 Electron archive and verified its pinned SHA-256. The extracted developer runtime had an ad hoc linker signature without a resource seal. Bundle verification and the standard system assessment returned the same resource error, so the reference Mac stopped before launch. [Reference Mac staging receipt](evidence/benchmark-v1/electron-external-input-0c279d9.json)

The owned development fixture packages the existing fixture sources inside a separate app and signs its nested code and resources. The packaged app passed strict recursive verification and its exact identifier check on hosted macOS 15.8.2 arm64. The automated keyboard action cleared the occlusion and the installed reference CLI still reported clipping. [Hosted signing and capture receipt](evidence/benchmark-v1/electron-packaged-5512f1d.json)

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

### Hosted Chrome toolbar activation

On `6a64796`, Chrome loaded the synthetic dispatch fixture and exposed its
seeded field in the debugging session. The OS shortcut produced no toolbar
popup during the ten-second observation window. The run stopped before
scanning. The revised harness finds the visible window by Chrome PID and
fixture title, checks X11 focus immediately before sending the shortcut,
and records bounded retries when no popup appears. The pasted-URL path
also verifies that it opens a fresh popup after the first one closes.
Both journeys still have to save a review and pass the masking and keyboard
checks. [Failed job and receipt](https://github.com/chrismicah/design-mcp/actions/runs/45164010853/job/137656215286)

The shortcut reached the fixture window on the next two runs. One run
saw a popup that disappeared before the first idle observation, and the
managed X11 run saw no usable popup. The hosted test now invokes the
installed action with a real click on a visible test icon. Keyboard
input still exercises scan, host recovery, both preview paths and saved
result navigation. The alternate invocation adds no site access and
leaves the shipped extension untouched. [Transient popup](https://github.com/chrismicah/design-mcp/actions/runs/45164436421) · [Managed X11 shortcut attempt](https://github.com/chrismicah/design-mcp/actions/runs/45164909456)
