# Running the paired benchmark

Use a clean checkout of the candidate to install the `design-mcp` executable into an isolated environment. Run `generate.py` with an authenticated subscription Codex client that supports the chosen model and effort. Supply the installed executable’s path. Keep the model, client version, asset policy, and task list fixed across candidates.

```bash
python3 evals/v1/generate.py \
  --out .context/benchmark/cells --server "$(command -v design-mcp)" \
  --model "$GENERATOR_MODEL" --effort max --jobs 2
```

Use repeated `--case` arguments to select named briefs. Run small batches when working within a subscription allowance. A complete cell is resumed from its receipt. A partially written cell stays in place. Use a new run directory for a retry and keep the earlier attempt.

To compare a credential-free stdio competitor, pass its installed executable to `--server`. Supply a JSON file with `--competitor-config`.

```json
{"name":"inspo","args":[],"env":{},"expected_tool":"search_screens"}
```

Use a separate output directory for each comparison. With `--treatment-only`, copy the original control cells and their receipts into that directory and retain the same prompt, client, model, and effort. Run the judge with `--treatment inspo` to match this example. Choose files and local launch wrappers with read-only tool access and a clean environment. Keep credential or approval failures in the results.

If a pinned stdio competitor omits read-only annotations, inspect its implementation and record the specific read-only tools in `verified_read_only_tools`. The benchmark only exposes those tools and uses non-interactive approval for that list. This setting applies to one benchmark client. [Codex tool configuration](https://learn.chatgpt.com/docs/extend/mcp#other-configuration-options)

Use `--no-shell` on both generation arms of a fresh comparison when the generator has called the command tool. This disables command execution in the client and records the setting. The judge rejects a pair with different shell settings. [Codex feature flags](https://learn.chatgpt.com/docs/config-file/config-basic#common-feature-flags)

For a public credential-free hosted comparator, use `--server-url` in place of `--server`. Keep its name distinct from the stdio variant. Record the reported server build, tool, and observation date. Compare either to the plain generator or to the fixed Design MCP arm while preserving the exact browser and generator settings.

To compare two Design MCP builds, use the candidate's executable with `--treatment-only --treatment-label candidate`. Copy the sealed `v2` cells into the same run and judge with `--control v2 --treatment candidate`. This keeps the MCP server and tool names consistent across the two builds.

Install `playwriter@0.12.0` in an isolated npm prefix. Run the renderer using a Python environment containing FastMCP, with Chrome installed locally. The supplied scratch directory must be new so that Chrome starts with an empty profile.

```bash
python3 evals/v1/render.py \
  --cells .context/benchmark/cells --scratch .context/benchmark/chrome \
  --playwriter "$PLAYWRITER_EXECUTABLE"

python3 evals/v1/judge.py \
  --cells .context/benchmark/cells --out .context/benchmark/judge \
  --model "$JUDGE_MODEL" --effort max
```

The renderer starts its own Chrome and Playwriter processes and shuts them down when it finishes. The judge verifies screenshot and HTML hashes. `judge/summary.json` records coverage, paired scores and each cell’s token receipt. Retain the generation and judging traces for any published score. [Scoring rubric](rubric.md)

Use `audit_scoreboard.py` to export completed frozen-baseline ballots without making new model calls. Give it the combined captures, the original generation runs, the blind ballots, and the downloaded capture artifacts in separate folders named by GitHub Actions run ID. It checks the generation trace, judge trace, blind images, and exact hosted archive before attaching a run link. The report retains the number of completed pairs out of the original 36.

```bash
python3 evals/v1/audit_scoreboard.py --cells "$COMBINED_CAPTURES" \
  --generation "$GENERATOR_RUN" --ballots "$JUDGE_RUN" \
  --archives "$DOWNLOADED_CAPTURES" --report "$REPORT"
```

Both arms must match the frozen brief, generator, client, effort, and browser pins. The judge keeps the first staged blind images for each ballot and records hashes for all four attached images. Use a fresh judging directory when an input changes.

For a comparator that reuses the frozen `v2` controls, set `--control v2 --treatment COMPETITOR`. Supply `--control-generation` for the frozen traces and `--control-archive` and `--treatment-archive` for the two downloaded run directories. The report still shows coverage against the 36 frozen briefs.

To measure retrieval before spending generation tokens, run `probe_competitors.py` against the installed competitor. It submits all 36 unedited briefs to the named search tool, requests the first three results, and records elapsed time, payload size, outcome, and ranked reference IDs. This probe measures search availability and coverage. The visual comparison still uses the generator and blinded judge.

The parser and scoring tests run without subscriptions or Chrome.

```bash
python3 -m unittest discover -s evals/v1 -v
```

## Connect Playwriter

For repeatable screenshots and benchmarks, use the isolated renderer above. It connects to a disposable Chrome profile through Playwriter's direct session.

For interactive debugging, install Playwriter's Chrome extension and click its icon on the intended test tab. When the icon turns green, add the pinned stdio server to your client and start a new session. [Playwriter extension](https://chromewebstore.google.com/detail/playwriter/jfeammnjpkecdekppnclgkkffahnhfhe) · [Pinned Playwriter MCP guide](https://github.com/remorses/playwriter/blob/playwriter%400.12.0/MCP.md)

```sh
# Codex
codex mcp add playwriter -- npx -y playwriter@0.12.0

# Claude Code
claude mcp add -s user playwriter -- npx -y playwriter@0.12.0
```

Call `session_list` to identify the connected browser, then verify the intended tab's URL and one visible heading before interacting. If the agent cannot see the tab, confirm the extension is active on that tab and reconnect the session. For the launch proof, run the actual installation and final user flow with GPT Computer Use and save a separate receipt. [Development harness](../../DESIGN-HARNESS.md)
