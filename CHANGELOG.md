# Changelog

- Made the reviewed catalog the default on the rebuild branch and retained the historical tools under explicit compatibility modes. Added local website, Chrome extension, SwiftUI and Electron review. The combined package passed eight clean-install jobs on macOS 15. [Rollout receipts](CONTENT-AUDIT.md) · [Review receipts](SMOKE-RECEIPTS.md)

## Unreleased

- Show the page-load error and recovery when Chrome cannot capture a pasted URL. The local reviewer saves a preview only after a successful capture.

- Removed duplicate offline vision queues from the package source and an obsolete failed transcript from the checkout. The offline scripts continue to use the canonical root queues. The wheel excludes both queues and the legacy pattern snapshot. [Corpus audit](CONTENT-AUDIT.md)

- Run the install, browser, and desktop checks against the pull request head. Align both README installers and the Chrome and MCP review instructions with one verified source tree. [Release candidate proof](SMOKE-RECEIPTS.md#release-candidate-on-both-architectures)

- Added `design-mcp serve --review` for image-capable MCP clients. `review_page` returns a masked screenshot and layout facts at desktop or mobile width. The default catalog stays at three tools. [Review workflow](design_mcp/review/README.md#visual-critique-and-a-live-task) · [Protocol proof](evidence/benchmark-v1/mcp-page-review.json)

- **Review URL** in Chrome now starts a local scan and opens a result tab with a masked capture and measured findings. It uses a disposable Chrome profile and works without Playwriter. The popup distinguishes a completed check with no findings from a failed scan.

- Record Chrome, Playwriter, navigation, capture, and preview timings for pasted-URL review. The hosted comparisons retained the same desktop and mobile images. The concurrent startup and direct MCP client trials missed their speed gate and were reverted. [Stage profile](evidence/benchmark-v1/public-url-stage-profile.json) · [Startup trial](evidence/benchmark-v1/public-url-overlap-trial.json) · [Client trial](evidence/benchmark-v1/public-url-mcp-sdk-trial.json)

- Check resolved destinations before opening the disposable review browser's TCP connections. Hosted Chrome blocked both private fixture targets and matched the previous public desktop and mobile captures. [Browser proof](evidence/benchmark-v1/browser-public-network-7bccfc1.json)

- Added an opt-in check for unhinted direction comparisons. The cold-storage runner keeps the exact brief and rejects hinted calls before browser review. All 72 frozen generator traces replayed with identical parser results. [Benchmark proof](evidence/benchmark-v1/unhinted-direct-gate.json)

- The CLI's `--playwriter` URL reviews use an isolated Playwriter session for each browser command and stop if request filtering fails to start. [Hosted review and regression checks](evidence/benchmark-v1/isolated-url-session-e1cd4eb.json)

- Keep previews and their 20-review retention limit inside an explicitly selected Chrome data directory. Reinstall an existing custom host to update its launcher. [Extension setup](design_mcp/review/README.md#set-up-the-extension)

- Added size-aware contrast checks to local review. Chrome flagged a 2.0-to-1 large label and previewed a recolor that meets its 3-to-1 minimum. [Browser and regression receipts](evidence/benchmark-v1/large-text-contrast.json)

- Added the 36-brief matched benchmark with clean-session token accounting, Playwriter captures, blind judging, and competitor adapters. All 36 verified pairs averaged 92.7 without the MCP and 94.1 with frozen v2. The paired 95% interval for the difference was −0.46 to +3.13 points. [Benchmark](EVALS.md)
- Added `design-mcp doctor`, offline directions, and lazy loading of the checksum-verified legacy corpus. Fresh pipx and uv installs exercised all 17 tools with Python 3.10–3.13 on both Intel and Apple Silicon macOS 15. The client examples use the installed command. [Install results](EVALS.md#candidate-decisions)
- Tested four credential-free design tools over stdio. In the first matched browser comparison, hosted Inspo scored 87.5 on ceramics and Design MCP scored 91.7. [Competitor results](teardown/COMPETITORS.md#visual-scoreboard)
- Measured compact computer-vision context against full-size screenshots and specified a fast local first review before frontier vision. [Vision research](research/VISION.md)
- Made the planner, builder, and independent evaluator workflow standard. Added recurring public source discovery and connected the visual release verdict to the exact browser captures. [Development harness](DESIGN-HARNESS.md)
- Added separate radio and service-booking directions. Both improved on the frozen v2 in their matched blind comparisons and passed keyboard task checks at desktop and mobile widths. [Visual and interaction results](EVALS.md#candidate-decisions)
- Updated the product direction to put price, shipping and the purchase action together on narrow screens. The ceramics comparison improved from 87.5 to 95.8 and its keyboard purchase passed at both widths. [Matched receipts](evidence/benchmark-v1/product-hero-visual.json)
- Tightened the train ticket direction around one departure and made the later departure time visible on the closed row. The repair scored 95.8 against 87.5 for both fresh controls and passed live reveal and collapse. [Repair receipts](evidence/rebuild/comparison/README.md#fresh-repair-comparison-against-v2-and-live-interaction)

- Added two form directions to the default library. The return-label rematch improved from 87.5 to 95.8, and the exhibition rematch tied at 91.7. All eight keyboard replays and all eight macOS 15 install jobs passed. [Candidate decisions](EVALS.md#candidate-decisions)
