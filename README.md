# Design MCP

Turn a brief into one sourced art direction. The response gives the coding agent a focal element, type pairing, color roles, layout and mobile order, an interaction, and a reason for the direction.

## Install

Install the verified development build with either command. Both support an explicit `--python` option to select an installed interpreter.

```bash
pipx install 'git+https://github.com/chrismicah/design-mcp.git@18b87522a49c545dd6204c20762d6fd64145d375'
# or
uv tool install 'git+https://github.com/chrismicah/design-mcp.git@18b87522a49c545dd6204c20762d6fd64145d375'
```

For a local checkout, pass `.` to your installer. [Candidate install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45196397946)

If Design MCP is already installed, add `--force` after `pipx install` or `uv tool install` in the matching command. Run `design-mcp doctor` and reconnect your MCP client after changing the installed version.

Run `design-mcp doctor` in the installed environment. It reports the interpreter and executable, validates bundled resources, and uses a local stdio client to discover the selected tools and call one. Each check reports pass, fail, or skip. A failed check gives a nonzero exit status.

If you see `Unknown command: doctor` or your client lists only the historical tools, run `command -v design-mcp` to see which launcher your shell found. Re-run the pinned install above with `--force` using the installer that owns that launcher. If you keep both installs, run `doctor` using the full path of the verified executable and use that same path as the MCP client's command. Reconnect and confirm that `direct`, `react`, and `check` appear. The old and new launchers can both report version `0.1.0`. [Launcher recovery test](evidence/benchmark-v1/stale-launcher-recovery.json)

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

The agent calls `direct` first. Give the audience, task, real content, and any existing brand constraints in the brief. Start with the brief alone so the tool can infer the surface. Use the optional surface argument when the project explicitly calls for one. A very short brief can produce one optional question with a default. If the brief asks for incompatible outcomes, have the agent ask which outcome to build. Apply the direction to the project's data, load its licensed typefaces, and test the main action.

| Tool | Arguments | Result |
| --- | --- | --- |
| `direct` | `brief`, optional `surface` and `avoid` | One reviewed direction and its evidence. Surfaces are `landing`, `dashboard`, `mobile` (web), `portfolio`, `pricing`, `editorial`, `form`. |
| `react` | `direction_id`, `reaction`, optional `comparison_id` | Concrete changes for “calmer”, “bolder”, “too generic”, or “more like A”. For a compared direction, pass its ID. |
| `check` | `source_code` | Located source findings for recognized font, copy, surface, and composition patterns. Use a rendered browser to check geometry, imagery, active fonts, motion, and usability. |

Try “calmer” after the first draft. The advice depends on the selected direction. On a form it suggests more space before a primary button. Other directions can adjust the type scale, accent, spacing, and motion. For the booking example, check that the chosen day appears beside the controls after selection on a phone. [Booking walkthrough and open checks](EVALS.md#candidate-decisions) · [Connected signup and dashboard tests](EVALS.md#connected-first-run-transfer)

## Review an existing interface

- **Measure the current Chrome tab or a pasted URL.** Load the folder printed by `design-mcp review --extension-path` as an unpacked extension and connect its local host once. Use **Review this page** for the active tab or **Review URL** for a pasted public address. Both paths save a masked capture. The popup reports measured overflow, covered controls, and contrast on flat backgrounds. After upgrading, reload the extension from the installed path and reconnect the local host. [Extension setup](design_mcp/review/README.md#set-up-the-extension)
- **Ask a vision-capable MCP client for a design critique.** Add `--review` to the installed server's `serve` arguments. Reconnect and use `review_page` to give the model a masked screenshot and layout facts. Connect Playwriter so the agent can also perform a visitor task and compare the resulting screens. [Setup and example prompt](design_mcp/review/README.md#visual-critique-and-a-live-task)
- **Capture both widths from the terminal.** With Playwriter 0.12.0 installed, run `design-mcp review https://example.com --playwriter`. The command uses a separate Chrome profile, checks the page at 1440 and 390 CSS px, and saves a local preview. [Browser setup](design_mcp/review/README.md)
- **Your SwiftUI or Electron app.** Copy the matching exporter from this repository into your UI test project. The Swift exporter needs an XCTest target. The Electron exporter reads a supplied BrowserWindow. Run `design-mcp review-app capture.json` to check recorded clipping and hittability. Keep raw desktop screenshots local, or redact visible input values before sharing. [Swift exporter](integrations/desktop/SwiftCapture.swift) · [Electron exporter](integrations/desktop/electron.mjs)

GPT Computer Use tested both Chrome flows on the earlier `0978712` build. The active-tab scan flagged **2.6:1 contrast** and opened a saved comparison that supports keyboard access. A pasted URL returned a **1440 × 900** capture in **6.37 seconds** with five fields masked. A 404 returned focus to the address field and left the saved reviews untouched. These are single walkthrough timings. [Native Chrome receipt](evidence/benchmark-v1/release-native-chrome-0978712.json)

At the install pin, macOS CI captured SwiftUI and Electron before and after a reveal action. SwiftUI went from four to five hittable buttons. Electron cleared the covered control finding and retained the clipping finding. The installed CLI reproduced both results from the exported geometry. [Desktop capture receipts](evidence/benchmark-v1/release-ci-18b87522.json)

## Compatibility

The default serves `direct`, `react`, and `check` from the reviewed catalog. Set `DESIGN_MCP_SURFACE=both` to add the 14 historical pattern, token, library, and analysis tools, or `legacy` for the historical tools alone. In the legacy search, request `visual_recipes` or `design_system` explicitly in `fields` to include the corresponding guidance.

The package requires Python 3.10 or later. Python 3.10 selects FastMCP 4.1.8. Python 3.11 and later select the 4.2 patch series starting at 4.2.4. [FastMCP 4.1.8](https://pypi.org/project/fastmcp/4.1.8/) · [FastMCP 4.2.4](https://pypi.org/project/fastmcp/4.2.4/)

Reviewed directions work offline. A checkout or older installation with the bundled pattern corpus uses its local copy. In a slim installation, the first tool call that needs historical patterns fetches 10,092,399 bytes from a pinned Git commit and verifies SHA-256 `dd51bf8db34f9295253b846ee8719cfd9b76b775ff029f591e49d9e7d16806a5`. Later calls use the local cache. [Pinned pattern corpus](https://github.com/chrismicah/design-mcp/blob/82fe6e3749acccf80aecfd523e531be4302865e3/design_mcp/data/patterns.json)

Plain `design-mcp doctor` works offline and checks the selected tool surface. In a legacy mode it also checks the corpus and local cache. Run `design-mcp doctor --repair` to prepare that cache before going offline or to replace a corrupt copy. Repair uses a verified bundle when available and otherwise needs access to the pinned download.

The new direction library and the historical pattern data have separate roles. Historical metadata may be templated, incomplete, or missing its original screenshot. Treat source records as review inputs. The directions carry observable source evidence or clearly labelled hypotheses. The direction and results can be checked separately.

### Existing source-checkout configurations

`python /path/to/design-mcp/server.py` still launches the 14-tool compatibility server. It uses the same implementation as the installed command. To move an existing configuration to the package, set `DESIGN_MCP_SURFACE=legacy` and use `design-mcp serve`. Use `both` to add the three direction tools. Old root-level `models` imports move to `design_mcp.models`.

The optional historical maintenance scripts write to `data/`. Run `python3 scripts/stage_legacy_data.py` from a source checkout before running those scripts. It seeds missing files from the verified snapshot and preserves any existing work. The MCP and review tools read their package resources independently.

## Verified results

At `18b87522`, all eight macOS 15 cells passed on Intel and Apple Silicon with Python 3.10–3.13. The logs verify **16 pinned Git installs, 16 doctor calls, and 96 stdio smoke runs**. The earlier `0978712` package passed **eight clean installs and 48 stdio checks** on Apple Silicon Ventura 13.7.4. Current-package Ventura runtime remains unverified on both architectures. [Exact macOS 15 matrix](evidence/benchmark-v1/release-ci-18b87522.json) · [Earlier Ventura matrix](evidence/benchmark-v1/ventura-tart-0978712.json)

On the Apple Silicon reference Mac, the installed pin reached its first `direct` result in a median **624 ms** across five fresh server processes. Fifteen warm calls took a median **1.65 ms**. The same install passed offline startup and an explicit legacy cache repair from the pinned download. [Offline and startup results](evidence/benchmark-v1/release-cache-18b87522.json)

The PR branch's work-order booking study kept the selected date and price visible at 320, 390, and 1440 px through the first draft and a one-word revision. Blind comparisons favored the revised guidance at both widths. Its package passed all 14 hosted checks at `a700f82`, including 16 macOS 15 clean installs, 96 stdio runs, both Chrome review flows, SwiftUI and Electron fixtures. [Booking comparison](evidence/benchmark-v1/booking-work-order-first.json) · [Hosted receipt](evidence/benchmark-v1/release-ci-a700f82.json) · [Exact follow-up CI at `559aee8`](evidence/benchmark-v1/release-ci-559aee8.json)

All 13 hosted checks passed at the install pin. The hosted Chrome extension reached a masked capture **2.36 seconds** after URL submission in that run. On the BenQ, the exact installed build saved and reopened both captures, switched to After by keyboard, and recovered in the same URL field after a 404. The native popup reported **0.74 seconds** for active-tab review and **1.37 seconds** for pasted URL review, one sample each. [Hosted checks](evidence/benchmark-v1/release-ci-18b87522.json) · [Native BenQ replay](evidence/benchmark-v1/release-native-benq-18b87522.json)

At the `18b87522` pin, `review_page` returned original masked PNGs at 1440 × 900 and 390 × 844. The stdio session recovered after an HTTP 404 and an unsupported URL. [Installed review receipt](evidence/benchmark-v1/release-ci-18b87522.json)

A standalone recovery comparison scored **8.20 desktop / 7.95 phone** for choosing a replacement tool and **7.80 at both widths** for recovering from a lift closure. Both prototypes passed scripted keyboard and touch checks. The installed MCP has a separate benchmark. [Prototype ballots and scope](EVALS.md#standalone-cabinet-and-train-recovery-repairs)

All 36 matched design briefs have blinded scores. The plain generator averaged 92.7 and frozen Design MCP v2 averaged 94.1, with 17 wins, 11 ties, and eight losses. The paired 95% interval of −0.46 to +3.13 points leaves the average advantage inconclusive. [Benchmark and receipts](EVALS.md)

The creative workflow tests different ways to present and use the same site before refining a candidate. Each scored round requires a fresh critic who uses the live site on desktop and phone. The verifier also keeps builder and critic sessions separate across rounds. [Creative round workflow](DESIGN-HARNESS.md#creative-rounds) · [Bakery study](EVALS.md#bakery-live-comparison) · [Editorial study](EVALS.md#creative-study-verification)

River's strongest fixture scored 8.85 from one critic and 8.75 from a second at both widths. A film-vault study tested five rounds and reached 8.45 at both widths in its strongest ballot. The release target is 9.5 from both critics. The daily source report collects leads from Show HN, research, and dated awards including Japan's MUUUUU.ORG. [Vault study](EVALS.md#vault-contact-strip-study) · [Festival study](EVALS.md#counterweight-festival-live-study) · [Creative research and reviews](research/CREATIVE-ROUNDS.md) · [Source review workflow](DESIGN-HARNESS.md#recurring-improvement)

The installed `18b87522` benchmark routed **15 of 36** briefs to the intended surface with only a brief supplied. It matched all six forms and six landing pages. Settings and empty states remain uncovered as exact surfaces. [Exact installed routing](https://github.com/chrismicah/design-mcp/blob/f009b852759f7427356cf08c307c68d904cb094b/evidence/benchmark-v1/release-direct-routing-18b87522.json) · [Earlier comparison](evidence/benchmark-v1/current-direct-routing.json)

In a targeted two-brief comparison, the radio and repair-shop directions averaged 97.9 versus 89.6 for frozen v2. The listening demo and booking summary passed keyboard checks at 1440 and 390 CSS px. [Matched visual results](evidence/benchmark-v1/specific-landing-visual.json) · [Browser actions](evidence/benchmark-v1/specific-landing-actions.json)

## Verify locally

From a source checkout with an active virtual environment, install the test dependencies and run the suites.

```bash
python -m pip install -e . pytest pytest-asyncio
python -m pytest tests evals
python scripts/smoke_design_mcp.py design-mcp serve
```

The smoke script exercises every tool in the selected mode. Set `DESIGN_MCP_SURFACE` to verify each mode. [Live smoke](SMOKE-RECEIPTS.md) · [Baseline](evidence/baseline/README.md) · [Comparison](evidence/rebuild/comparison/README.md) · [Corpus audit](CONTENT-AUDIT.md)

The development harness covers visual review, Playwriter setup, GPT Computer Use acceptance, and recurring public source discovery. [Development harness](DESIGN-HARNESS.md) · [Connect Playwriter](evals/v1/README.md#connect-playwriter) · [Release gates](RELEASE-GOAL.md#current-install-candidate)
