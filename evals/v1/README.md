# Running the paired benchmark

Use a clean checkout of the candidate to install the `design-mcp` executable into an isolated environment. Run `generate.py` with an authenticated subscription Codex client that supports the chosen model and effort. Supply the installed executable’s path. Keep the model, client version, asset policy, and task list fixed across candidates.

```bash
python3 evals/v1/generate.py \
  --out .context/benchmark/cells --server "$(command -v design-mcp)" \
  --model "$GENERATOR_MODEL" --effort max --jobs 2
```

Use repeated `--case` arguments to select named briefs. Run small batches when working within a subscription allowance. A complete cell is resumed from its receipt. A partially written cell stays in place. Use a new run directory for a retry and keep the earlier attempt.

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

The parser and scoring tests run without subscriptions or Chrome.

```bash
python3 -m unittest discover -s evals/v1 -v
```
