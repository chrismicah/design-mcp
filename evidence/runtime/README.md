# Runtime audit proofs

Compact, reproducible evidence for `AUDIT.md`, captured at `82fe6e3`. Raw per-call tool outputs (69 files, about 2.6 MB) are not tracked; `probe.py` regenerates them.

| File | Contents |
|---|---|
| `probe.py` | Read-only harness. Calls all 14 tools, writes one JSON per call plus `summary.json` |
| `summary-source.json` | Run against the checked-out source |
| `summary-installed.json` | Run against an existing pipx install whose `server.py` hash matches the source. Not a fresh install |
| `tool-inventory-source.json` | Tool names, parameters, description and schema sizes as listed to a client |
| `facts-source.json` | Corpus distributions, payload breakdown, taxonomy mismatches, output keys |
| `slop-detection.json` | What the critique tools reported on the banned-tell sample in `probe.py` |
| `docs-install-facts.txt` | README claims against repository facts |
| `probe-stdio.py`, `installed-stdio.json` | Independent stdio handshake and custom-color request against the existing installed executable |
| `baseline-pytest.log` | Existing root test suite from local runtime and pytest dependencies |

Reproduce, from the repository root, with a Python that has `fastmcp` and `pydantic`:

    PYTHONPATH=$PWD python evidence/runtime/probe.py source /tmp/probe-source

Reading the numbers:

- `bytes` is the character length of the JSON-serialised result. `approx_tokens` is that length divided by 4. No tokenizer was run; real token counts are unknown.
- `tells` and `good` are regex match counts over the serialised output, using the patterns in `probe.py`. They are not a judgement of rendered design.
- `slop_sample_detection` inside the summaries is a substring check that also matches echoed input. Use `slop-detection.json` instead.
- Local user paths are redacted.
