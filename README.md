# Design MCP

Turn a brief into one sourced art direction. The response gives the coding agent a focal element, type pairing, color roles, layout and mobile order, an interaction, and a reason for the direction.

## Install

From a checkout with Python 3.12 or later, install with either `pipx install .` or `uv tool install .`. Verify the installed executable with `design-mcp version`.

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

> Make this look good. Build a theatre turnaround board so a stage manager can find the room that's running late. Studio B is six minutes late and Hall A is ready.

The agent calls `direct` first. Pass the audience, task, real content, and any existing brand constraints as ordinary language. A very short brief can produce one optional question with a default. Apply the direction to the project's data, load its licensed typefaces, and test the main action.

| Tool | Arguments | Result |
| --- | --- | --- |
| `direct` | `brief`, optional `surface` and `avoid` | One reviewed direction and its evidence. Surfaces are `landing`, `dashboard`, `mobile` (web), `portfolio`, `pricing`, `editorial`. |
| `react` | `direction_id`, `reaction`, optional `comparison_id` | Concrete changes for “calmer”, “bolder”, “too generic”, or “more like A”. For a compared direction, pass its ID. |
| `check` | `source_code` | Located source findings for recognized font, copy, surface, and composition patterns. Use a rendered browser to check geometry, imagery, active fonts, motion, and usability. |

Try “calmer” after the first draft. The result adjusts focal spacing, the size of the display type, accent use, and motion timing while preserving the product facts and main task.

## Compatibility

`DESIGN_MCP_SURFACE=v2` exposes the three tools above. `both` (the default) also exposes the 14 historical pattern, token, library, and analysis tools. `legacy` exposes only those historical tools. In the legacy search, request `visual_recipes` or `design_system` explicitly in `fields` to include the corresponding guidance.

The new direction library and the historical pattern data have separate roles. Historical metadata may be templated, incomplete, or missing its original screenshot. Treat source records as review inputs. The directions carry observable source evidence or clearly labelled hypotheses. The direction and results can be checked separately.

## Verified results

The pinned baseline passed 308 tests. Fresh pipx on Python 3.12.13 and uv on Python 3.13.3 each served 17/17 tools on Apple Silicon. Python 3.10 and 3.11 are excluded by the current package metadata. The 36-brief visual comparison and Intel coverage are in progress. [Benchmark and install receipts](EVALS.md)

## Verify locally

```bash
python -m pytest tests
python scripts/smoke_design_mcp.py design-mcp serve
```

The smoke script exercises every tool in the selected mode. Set `DESIGN_MCP_SURFACE` to verify each mode. [Live smoke](SMOKE-RECEIPTS.md) · [Baseline](evidence/baseline/README.md) · [Comparison](evidence/rebuild/comparison/README.md) · [Corpus audit](CONTENT-AUDIT.md)
