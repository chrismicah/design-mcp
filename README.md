# Design MCP

Turn a brief into one sourced art direction. The response gives the coding agent a focal element, type pairing, color roles, layout and mobile order, an interaction, and a reason for the direction.

## Install

Install the verified development build with either command. Both support an explicit `--python` option to select an installed interpreter.

```bash
pipx install 'git+https://github.com/chrismicah/design-mcp.git@6e9a239499d46bdf50f4896dcc70f3b6c0f0b7c8'
# or
uv tool install 'git+https://github.com/chrismicah/design-mcp.git@6e9a239499d46bdf50f4896dcc70f3b6c0f0b7c8'
```

For a local checkout, pass `.` to your installer. [Candidate install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45089158186)

Run `design-mcp doctor` in the installed environment. It reports the interpreter and executable, validates bundled resources, and uses a local stdio client to discover the selected tools and call one. Each check reports pass, fail, or skip. A failed check gives a nonzero exit status.

### Claude Code

```bash
claude mcp add design-mcp -s user -e DESIGN_MCP_SURFACE=v2 -- design-mcp serve
claude mcp get design-mcp
```

An alternative in an active virtual environment is `python -m pip install .`. Use the full path to `design-mcp` when it is outside the client's PATH. The MCP runs over stdio and the direction tools use bundled data. They require no API key.

### Codex

Add the server to your Codex configuration. The `writes` approval mode uses the read-only annotation on the three direction tools.

```toml
[mcp_servers.design-mcp]
command = "design-mcp"
args = ["serve"]
default_tools_approval_mode = "writes"

[mcp_servers.design-mcp.env]
DESIGN_MCP_SURFACE = "v2"
```

### Claude Desktop and Cursor

Add this entry to Claude Desktop’s `claude_desktop_config.json` or Cursor’s `.cursor/mcp.json`. Set `command` to the path printed by `command -v design-mcp` if the client launches outside your shell environment.

```json
{
  "mcpServers": {
    "design-mcp": {
      "command": "design-mcp",
      "args": ["serve"],
      "env": {"DESIGN_MCP_SURFACE": "v2"}
    }
  }
}
```

## Give the agent a brief

> I need a site for a local bike repair shop. Second Spin does 48-hour tune-ups for $85. We are at 41 Elm Street and take bookings Tuesday to Saturday. Make booking easy to find and let a visitor pick a day to see the booking summary.

The agent calls `direct` first. Pass the audience, task, real content, and any existing brand constraints as ordinary language. A very short brief can produce one optional question with a default. Apply the direction to the project's data, load its licensed typefaces, and test the main action.

| Tool | Arguments | Result |
| --- | --- | --- |
| `direct` | `brief`, optional `surface` and `avoid` | One reviewed direction and its evidence. Surfaces are `landing`, `dashboard`, `mobile` (web), `portfolio`, `pricing`, `editorial`, `form`. |
| `react` | `direction_id`, `reaction`, optional `comparison_id` | Concrete changes for “calmer”, “bolder”, “too generic”, or “more like A”. For a compared direction, pass its ID. |
| `check` | `source_code` | Located source findings for recognized font, copy, surface, and composition patterns. Use a rendered browser to check geometry, imagery, active fonts, motion, and usability. |

Try “calmer” after the first draft. The result adjusts focal spacing, the size of the display type, accent use, and motion timing while preserving the product facts and main task.

## Review an existing interface

- **Critique a website with your agent.** Add `--review` to the installed MCP server's `serve` arguments to enable `review_page`. Reconnect the client and ask it to inspect the masked screenshot and layout facts. Connect Playwriter so the agent can perform a visitor task and compare the resulting screens. [Setup and example prompt](design_mcp/review/README.md#visual-critique-and-a-live-task)
- **Paste a URL in Chrome.** Open the extension, paste the address and press **Review URL**. The result tab shows the masked capture and its first measured issue, or a summary of the checks that ran. After upgrading, reload the unpacked extension from the installed path and reconnect its local host. [Extension setup](design_mcp/review/README.md#set-up-the-extension) · [Installed Chrome test](evidence/benchmark-v1/chrome-review-url-one-submit.json)
- **A public website.** With Playwriter 0.12.0 installed, run `design-mcp review https://example.com --playwriter`. The command uses a separate Chrome profile, saves a local preview, and reports any measured finding. [Browser setup](design_mcp/review/README.md)
- **The active Chrome tab.** Load the extension from the folder printed by `design-mcp review --extension-path`. Open the toolbar popup, choose **Review this page**, and follow its one-time host setup. [Extension setup](design_mcp/review/README.md#set-up-the-extension)
- **Your SwiftUI or Electron app.** Copy the matching exporter from this repository into your UI test project. The Swift exporter needs an XCTest target. The Electron exporter reads a supplied BrowserWindow. Run `design-mcp review-app capture.json` to check recorded clipping and hittability. [Swift exporter](integrations/desktop/SwiftCapture.swift) · [Electron exporter](integrations/desktop/electron.mjs)

GPT Computer Use verified the `f17bd6f` Chrome extension on the reference Mac. It loaded the extension in a disposable profile, recovered from a missing native host, found the seeded contrast issue, switched to After by keyboard, and reopened the same preview with the field masked. Across 30 separate popup opens in the running browser, p95 was **136 ms to Scan** and **100 ms from Scan to the first finding**. These measurements use the visible controls exposed through Accessibility. The `7bccfc1` install passed the hosted public URL check at desktop and mobile widths and refused both owned private fixture targets. [Reference Mac walkthrough](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json) · [Timing receipt](evidence/benchmark-v1/chrome-reference-latency-f17bd6f.json) · [Public URL receipt](evidence/benchmark-v1/browser-public-network-7bccfc1.json)

On a hosted Mac, ten fresh Chrome profiles took a median **7.68 seconds** each to review the same public URL at both widths and save the local preview. All ten produced the expected masked images. [Public URL timing](evidence/benchmark-v1/public-url-paired-timing.json)

GPT Computer Use tested the earlier two-step pasted-address flow on `7bccfc1`. It opened the public address form, pressed the toolbar Scan action, and reloaded the locally saved preview. The scan reported four masked fields in 184 ms after the page was already open. The same install separately captured the page with Playwriter at desktop and mobile widths. [Reference Mac proof](evidence/benchmark-v1/reference-mac-pasted-url-7bccfc1.json)

GPT Computer Use also exercised the SwiftUI and Electron fixtures on the reference Mac. SwiftUI exposed a new control after Reveal, and the installed CLI counted five then six controls in the hosted geometry captures. In Electron, Tab and Return revealed the covered button. The installed CLI reviewed the fresh local captures and reported that occlusion cleared while clipping persisted. [SwiftUI evidence](evidence/benchmark-v1/reference-mac-desktop-f17bd6f.json) · [Electron evidence](evidence/benchmark-v1/reference-mac-electron-f17bd6f.json)

## Compatibility

The default serves `direct`, `react`, and `check` from the reviewed catalog. Set `DESIGN_MCP_SURFACE=both` to add the 14 historical pattern, token, library, and analysis tools, or `legacy` for the historical tools alone. In the legacy search, request `visual_recipes` or `design_system` explicitly in `fields` to include the corresponding guidance.

The package requires Python 3.10 or later. Python 3.10 selects FastMCP 4.1.8. Python 3.11 and later select the 4.2 patch series starting at 4.2.4. [FastMCP 4.1.8](https://pypi.org/project/fastmcp/4.1.8/) · [FastMCP 4.2.4](https://pypi.org/project/fastmcp/4.2.4/)

Reviewed directions work offline. A checkout or older installation with the bundled pattern corpus uses its local copy. In a slim installation, the first tool call that needs historical patterns fetches 10,092,399 bytes from a pinned Git commit and verifies SHA-256 `dd51bf8db34f9295253b846ee8719cfd9b76b775ff029f591e49d9e7d16806a5`. Later calls use the local cache. [Pinned pattern corpus](https://github.com/chrismicah/design-mcp/blob/82fe6e3749acccf80aecfd523e531be4302865e3/design_mcp/data/patterns.json)

Plain `design-mcp doctor` works offline and checks the selected tool surface. In a legacy mode it also checks the corpus and local cache. Run `design-mcp doctor --repair` to prepare that cache before going offline or to replace a corrupt copy. Repair uses a verified bundle when available and otherwise needs access to the pinned download.

The new direction library and the historical pattern data have separate roles. Historical metadata may be templated, incomplete, or missing its original screenshot. Treat source records as review inputs. The directions carry observable source evidence or clearly labelled hypotheses. The direction and results can be checked separately.

## Verified results

All eight macOS 15 clean-install jobs passed on Intel and Apple Silicon with Python 3.10–3.13. These runs installed a GitHub test merge with the same source tree as the pinned revision. Both installers passed `doctor`, exercised all 17 tools in combined mode and checked the opt-in browser tool's error response. An installed local copy of the pin returned masked public-page screenshots through MCP at desktop and mobile widths. Ventura dependency resolution passed on both architectures. Ventura runtime and fresh Tart verification remain open. [Candidate install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45089158186) · [Installed screenshot receipt](evidence/benchmark-v1/release-initial-6e9a239.json) · [Ventura preflight](evidence/benchmark-v1/ventura-wheel-preflight.json)

All 36 matched design briefs have blinded scores. The plain generator averaged 92.7 and frozen Design MCP v2 averaged 94.1, with 17 wins, 11 ties, and eight losses. The paired 95% interval of −0.46 to +3.13 points leaves the average advantage inconclusive. [Benchmark and receipts](EVALS.md)

The pinned install routed **15 of 36** briefs to the matching surface with only a brief supplied, up from **9 of 36** in frozen v2. All six forms routed correctly. Settings and empty states remain uncovered as exact surfaces. [Current installed routing](evidence/benchmark-v1/release-initial-6e9a239.json) · [Earlier comparison](evidence/benchmark-v1/current-direct-routing.json)

In a targeted two-brief comparison, the radio and repair-shop directions averaged 97.9 versus 89.6 for frozen v2. The listening demo and booking summary passed keyboard checks at 1440 and 390 CSS px. [Matched visual results](evidence/benchmark-v1/specific-landing-visual.json) · [Browser actions](evidence/benchmark-v1/specific-landing-actions.json)

## Verify locally

From a source checkout with an active virtual environment, install the test dependencies and run the suites.

```bash
python -m pip install -e . pytest pytest-asyncio
python -m pytest tests evals
python scripts/smoke_design_mcp.py design-mcp serve
```

The smoke script exercises every tool in the selected mode. Set `DESIGN_MCP_SURFACE` to verify each mode. [Live smoke](SMOKE-RECEIPTS.md) · [Baseline](evidence/baseline/README.md) · [Comparison](evidence/rebuild/comparison/README.md) · [Corpus audit](CONTENT-AUDIT.md)

The development harness covers visual review, Playwriter setup, GPT Computer Use acceptance, and recurring public source discovery. [Development harness](DESIGN-HARNESS.md) · [Connect Playwriter](evals/v1/README.md#connect-playwriter)
