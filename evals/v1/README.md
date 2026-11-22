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

For the shadcn 4.23.0 maintenance comparison, use an isolated fixture configured for the official registry. Run with `--case form-maintenance --treatment-only --competitor-config evals/v1/shadcn-maintenance.json` and pass the fixture's launch wrapper as `--server`. The config's `required_shadcn_items` declares the relevant registry items and example IDs. The runner keeps the trace and HTML and requires a matching item in a successful tool response before rendering. An item name echoed in a query or an empty result does not qualify. [Maintenance registry receipt](../../evidence/benchmark-v1/shadcn-maintenance-registry.json)

To reproduce the separate retrieval comparison, run `probe_registry_and_skill.py shadcn --task-queries` against the same installed fixture. It uses the 36 frozen briefs, one registered short phrase per case, and that case's first registered component name. The result records relevant items, response size, and elapsed time for all three. [Installed results](../../evidence/benchmark-v1/shadcn-named-component-retrieval.json)

Use `--no-shell` on both generation arms of a fresh comparison when the generator has called the command tool. This disables command execution in the client and records the setting. The judge rejects a pair with different shell settings. [Codex feature flags](https://learn.chatgpt.com/docs/config-file/config-basic#common-feature-flags)

For a public credential-free hosted comparator, use `--server-url` in place of `--server`. Keep its name distinct from the stdio variant. Record the reported server build, tool, and observation date. Compare either to the plain generator or to the fixed Design MCP arm while preserving the exact browser and generator settings.

For the Storybook 10.6.0 gallery comparison, start the owned fixture from `storybook-fixture/` using the pinned packages and loopback startup in the CI recipe. Use the original gallery v2 control from run 45002279105 with its generation trace. Keep its Codex 0.170.0, GPT-6.2 Astra max, shell-disabled, Chrome 158.0.8127.36 and Playwriter 0.12.0 settings. [Fixture startup](../../.github/workflows/storybook-mcp-probe.yml) · [Verified control and trace replay](../../evidence/benchmark-v1/storybook-gallery-preflight.json)

```sh
python3 evals/v1/generate.py \
  --out "$STORYBOOK_GALLERY_RUN" --loopback-server-url http://127.0.0.1:6006/mcp \
  --competitor-config evals/v1/storybook-gallery.json --case mobile-gallery \
  --treatment-only --no-shell --model gpt-6.2-astra --effort max --quota-probe "$QUOTA_PROBE"
```

The client exposes only the three reviewed docs tools. The treatment must retrieve the pinned disclosure component or story text. Listing the catalog or returning an error leaves the generation ineligible for rendering. The fixture contributes a disclosure interaction and the prompt supplies the gallery facts. Exercise the keyboard reveal, collapse and focus at both widths before blind scoring. This run compares one gallery brief.

To compare two Design MCP builds, use the candidate's executable with `--treatment-only --treatment-label candidate`. Copy the sealed `v2` cells into the same run and judge with `--control v2 --treatment candidate`. This keeps the MCP server and tool names consistent across the two builds.

For a routing candidate, set `--expect-direction CASE=ID` once per selected case before generation. The generator still sees the original brief. The runner keeps the trace and HTML and marks a treatment ineligible for judging unless its single completed `direct` reply selected that ID.

For the held-out cold-storage comparison, also pass `--require-unhinted-direct` in both generation runs. The generator receives the same instruction in every arm. The trace must show one `direct` call whose only argument is the verbatim `brief`. Both the original report and any ineligible draft are retained. Set `require_unhinted_direct` to `true` in the private live-review specification to replay this check before opening a browser.

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

### Compact live review

Use the opt-in adapter to give an independent critic a bounded set of browser controls during development. Serve the anonymous fixtures on loopback and start a dedicated headless Chrome with an empty profile and a loopback CDP listener. Start Playwriter 0.12.0 on its own loopback relay port. Keep the pairing key outside the critic's prompt.

Configure the adapter with the pinned executable in `playwriter`, the integer `relay_port`, and the exact loopback WebSocket URL from Chrome's `/json/version` in `cdp`. Set `pages` to a map from neutral IDs to full loopback fixture URLs and `evidence_dir` to an empty directory beneath the client's working directory. Launch it as a stdio server in the installed test environment.

```sh
python -B evals/v1/live_browser.py --config "$REVIEW_CONFIG"
```

The critic uses `open_view`, `act`, and `capture`. Complete one view before opening the next. Each open starts with fresh fixture storage, while a reload through `act` preserves it. By default, capture returns a compact preview and archives the original PNG with its hash. Set `"original_capture": true` for release review to send the archived PNG itself to the critic. Keep `audit.jsonl`, the critic trace, and the original images together. [Real driver probe](../../evidence/benchmark-v1/compact-live-browser-probe.json) · [Blind comparison](../../evidence/benchmark-v1/compact-live-repair-ballot.json)

Use `audit_scoreboard.py` to export completed frozen-baseline ballots without making new model calls. Give it the combined captures, the original generation runs, the blind ballots, and the downloaded capture artifacts in separate folders named by GitHub Actions run ID. It checks the generation trace, judge trace, blind images, and exact hosted archive before attaching a run link. The report retains the number of completed pairs out of the original 36.

```bash
python3 evals/v1/audit_scoreboard.py --cells "$COMBINED_CAPTURES" \
  --generation "$GENERATOR_RUN" --ballots "$JUDGE_RUN" \
  --archives "$DOWNLOADED_CAPTURES" --report "$REPORT"
```

Both arms must match the frozen brief, generator, client, effort, and browser pins. The judge keeps the first staged blind images for each ballot and records hashes for all four attached images. Use a fresh judging directory when an input changes.

For a comparator that reuses the frozen `v2` controls, set `--control v2 --treatment COMPETITOR`. Supply `--control-generation` for the frozen traces and `--control-archive` and `--treatment-archive` for the two downloaded run directories. The report still shows coverage against the 36 frozen briefs.

To measure retrieval before spending generation tokens, run `probe_competitors.py` against the installed competitor. It submits all 36 unedited briefs to the named search tool, requests the first three results, and records elapsed time, payload size, outcome, and ranked reference IDs. This probe measures search availability and coverage. The visual comparison still uses the generator and blinded judge.

The parser, scoring, and browser-adapter tests use synthetic fixtures. Install the test dependencies from the source checkout first. [Local test setup](../../README.md#verify-locally)

```bash
python -m pytest evals/v1
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
