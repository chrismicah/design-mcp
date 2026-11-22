# Design MCP

Turn a brief into one sourced art direction. The response gives the coding agent a focal element, type pairing, color roles, layout and mobile order, an interaction, and a reason for the direction.

## Install

Install the verified development build with either command. Both support an explicit `--python` option to select an installed interpreter.

```bash
pipx install 'git+https://github.com/chrismicah/design-mcp.git@f17bd6f79fff62d1ec3e051b29d930ccb32b3a46'
# or
uv tool install 'git+https://github.com/chrismicah/design-mcp.git@f17bd6f79fff62d1ec3e051b29d930ccb32b3a46'
```

For a local checkout, pass `.` to your installer. [Verified installs](evidence/benchmark-v1/direct-git-install-f17bd6f.json)

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

- **A public website.** Run `design-mcp review https://example.com --playwriter /path/to/playwriter`. The command uses a separate Chrome profile, saves a local preview, and reports any measured finding. [Browser setup](design_mcp/review/README.md)
- **The active Chrome tab.** Load the extension from the folder printed by `design-mcp review --extension-path`. Open the toolbar popup, choose **Review this page**, and follow its one-time host setup. [Extension setup](design_mcp/review/README.md#set-up-the-extension)
- **Your SwiftUI or Electron app.** Use the app-specific exporter, then run `design-mcp review-app capture.json` to check the visible controls for clipping and occlusion. [Swift exporter](integrations/desktop/SwiftCapture.swift) · [Electron exporter](integrations/desktop/electron.mjs)

Hosted checks covered a public URL on macOS, the Chrome extension on Linux and macOS 15 arm64, and owned SwiftUI and Electron fixtures on macOS 15 arm64. The installed candidate passed three hosted Mac Chrome runs from toolbar click through keyboard Before and After and reopening the preview from its own profile. The first archived preview passed field masking. Reference-Mac latency, independent design review, and final GPT Computer Use smoke remain open. [Chrome evidence](evidence/benchmark-v1/chrome-profile-review-isolation.json) · [Smoke receipts](SMOKE-RECEIPTS.md)

## Compatibility

The default serves `direct`, `react`, and `check` from the reviewed catalog. Set `DESIGN_MCP_SURFACE=both` to add the 14 historical pattern, token, library, and analysis tools, or `legacy` for the historical tools alone. In the legacy search, request `visual_recipes` or `design_system` explicitly in `fields` to include the corresponding guidance.

The package requires Python 3.10 or later. Python 3.10 selects FastMCP 4.1.8. Python 3.11 and later select the 4.2 patch series starting at 4.2.4. [FastMCP 4.1.8](https://pypi.org/project/fastmcp/4.1.8/) · [FastMCP 4.2.4](https://pypi.org/project/fastmcp/4.2.4/)

Reviewed directions work offline. A checkout or older installation with the bundled pattern corpus uses its local copy. In a slim installation, the first tool call that needs historical patterns fetches 10,092,399 bytes from a pinned Git commit and verifies SHA-256 `dd51bf8db34f9295253b846ee8719cfd9b76b775ff029f591e49d9e7d16806a5`. Later calls use the local cache. [Pinned pattern corpus](https://github.com/chrismicah/design-mcp/blob/82fe6e3749acccf80aecfd523e531be4302865e3/design_mcp/data/patterns.json)

Plain `design-mcp doctor` works offline and checks the selected tool surface. In a legacy mode it also checks the corpus and local cache. Run `design-mcp doctor --repair` to prepare that cache before going offline or to replace a corrupt copy. Repair uses a verified bundle when available and otherwise needs access to the pinned download.

The new direction library and the historical pattern data have separate roles. Historical metadata may be templated, incomplete, or missing its original screenshot. Treat source records as review inputs. The directions carry observable source evidence or clearly labelled hypotheses. The direction and results can be checked separately.

## Verified results

The pinned Git commands passed all eight clean-install jobs on Intel and Apple Silicon macOS 15 with Python 3.10–3.13. Each installer verified the package commit, passed `doctor` and exercised all 17 compatibility tools. The macOS 13 dependency preflight passed all eight wheel checks. Ventura runtime and fresh Tart verification remain open. [Install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45026602037) · [Ventura preflight](evidence/benchmark-v1/ventura-wheel-preflight.json)

All 36 matched design briefs have blinded scores. The plain generator averaged 92.7 and frozen Design MCP v2 averaged 94.1, with 17 wins, 11 ties, and eight losses. The paired 95% interval of −0.46 to +3.13 points leaves the average advantage inconclusive. [Benchmark and receipts](EVALS.md)

The current install routed **15 of 36** briefs to the matching surface with only a brief supplied, up from **9 of 36** in frozen v2. All six forms routed correctly. Settings and empty states remain uncovered as exact surfaces. [Installed routing comparison](evidence/benchmark-v1/current-direct-routing.json)

The current radio and repair-shop directions averaged 97.9 versus 89.6 for the frozen v2 on those two briefs. The listening demo and booking summary also passed keyboard checks at 1440 and 390 CSS px. [Matched visual results](evidence/benchmark-v1/specific-landing-visual.json) · [Browser actions](evidence/benchmark-v1/specific-landing-actions.json)

## Verify locally

From a source checkout with an active virtual environment, install the test dependencies and run the suites.

```bash
python -m pip install -e . pytest pytest-asyncio
python -m pytest tests evals
python scripts/smoke_design_mcp.py design-mcp serve
```

The smoke script exercises every tool in the selected mode. Set `DESIGN_MCP_SURFACE` to verify each mode. [Live smoke](SMOKE-RECEIPTS.md) · [Baseline](evidence/baseline/README.md) · [Comparison](evidence/rebuild/comparison/README.md) · [Corpus audit](CONTENT-AUDIT.md)

The development harness covers visual review, Playwriter setup, GPT Computer Use acceptance, and recurring public source discovery. [Development harness](DESIGN-HARNESS.md) · [Connect Playwriter](evals/v1/README.md#connect-playwriter)
