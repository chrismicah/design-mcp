# Design MCP rebuild plan

**Approved by the owner on 2026-11-20.** Run A–G on stacked branches. If the direction engine improves on the baseline, continue through corpus exclusions, rewrites from verified sources, expansion, adversarial QA, and the full real-client smoke run. If the comparison falls short, document why, fix the failure, and rerun the affected cases. The standing branch, credential and spending rules apply.
Baseline `82fe6e3`. This proposal incorporates the runtime and corpus audits, seven research files, and the independent pre-approval review. [Runtime audit](AUDIT.md) · [Corpus audit](CONTENT-AUDIT.md) · [Research](research/) · [Review](evidence/REVIEW.md)

## 1. Approach

Start with a measured six-brief comparison and use the result to guide the full rebuild. Preserve a reversible legacy surface during migration.

| New tool | Does | Response cap |
|---|---|---|
| `direct` | brief → one art direction, with at most two multiple-choice questions that each state a default | 6,000 characters |
| `react` | direction + `calmer` / `bolder` / `too generic` / `more like <id>` → revised direction and expected visible differences | 3,200 characters |
| `check` | HTML/JSX/CSS → static tell findings with rule id and line | 2,400 characters |

A direction record uses the six fields in `RESEARCH-UI.md` plus rationale, citations with a strength label (`evidence`, `hypothesis`, `house target`), source ids, and reviewer. The server instructions and README make `direct` the first call for a new brief. Preserve a reversible default and ask a question only when its answer changes the chosen composition or primary action.

## 2. Compatibility during the pilot

- All 14 current tools stay registered through the pilot. A setting selects `legacy`, `both` or `v2`; default `both`. Switching back is a config change.
- Fixes to legacy tools are limited to defects with runtime proof: the two unpackaged imports and the embedded boilerplate in search results (AUDIT §2).
- Before any tool is retired, record its callers: README examples, the three prompt files, tests, and client configs that name it. External callers are unknown. Keep the legacy switch while clients migrate and document any eventual deprecation with the replacement tool.

## 3. Corpus and cull procedure

- The revised rubric covers 7,080 pattern rows. It identifies 6,285 cull candidates, 277 conditional on source recovery, 26 duplicate merges, 470 candidates to rewrite from source and 22 textual references. Zero qualify for the new library as written. [Actions](evidence/content/action_list.csv)
- During the pilot, the new entry point reads only the six reviewed directions. Before broad rollout, checkpoint the baseline and apply exclusions through a reversible manifest. Remove excluded records from the new runtime library and keep their original source in Git history. Keep useful legacy data available while the compatibility switch is supported.
- Choose each rewrite candidate for a demonstrated need and a verifiable source. Require the full art-direction record and separate review. Resize the corpus based on coverage and benchmark results.

## 4. Slices

Each slice is one branch **stacked on the previous slice's verified commit** (its check passed and a reviewer file exists). A failed slice blocks its dependants; nothing branches from unverified work. Checks are internal, not owner gates.

| Slice | Work | Check (proof file) |
|---|---|---|
| A Baseline | Six briefs × two arms (no MCP, current MCP), same model and prompt. Static tells on all 12 outputs; render three briefs per arm at 1440 and 390 | `evidence/baseline/`: prompts, outputs, findings, six render pairs |
| B Design checks | Static tell rules with fixtures (banned sample, Trackr, clean cases) | Fixture results; false-positive list |
| C Pilot records | **One direction per brief (six)**, authored from a verified source | Schema pass, static check, one different-session review file each |
| D Engine | `direct`, `react`, `check` behind the surface setting | Six briefs: caps met, zero static tells, each reaction changes its listed fields only |
| E Ablation | Same three briefs as A, pilot arm, plus one arm with rationale and citations stripped | Paired renders with provenance hidden; scores; similarity across outputs |
| F Sample fixes + challenger | Fix what E found; one challenger session per lane attacks its output once | Findings fixed or rebutted in writing |
| G Decide | Coordinator compares E and F against A | Written recommendation: expand, change, or stop |

Size expansion from the pilot results. Require a passing first render for clear briefs and a passing, visibly improved render within two quick reactions for vague ones. Measure elapsed time from the initial prompt to first rendered pass, question count and reactions. Review initial pilot pass rate and diversity against the no-MCP and legacy arms. If the pilot misses, use the written findings to narrow the next fix and rerun the affected paired cases.

Before launch, run all six briefs across the clear, vague, misleading and minimal-input cases. Use separate adversarial reviewers to file every failure and retest it after fixes. The final GPT computer-use lane runs last under a short checklist, installs from the README in a fresh clone and real client, exercises every exposed tool, and saves scored desktop and 390 px screenshots, the font check, blur, tell sweep, award comparisons and suite results in `SMOKE-RECEIPTS.md`. Allow native mobile claims only with separate native device or simulator evidence. [Final acceptance brief](research/RESEARCH-USER.md#acceptance-experiment)

## 5. Proof types

| Claim | Proof required |
|---|---|
| Banned font, gradient class, glass utility, banned copy, emoji bullet, exclamation CTA | **Static**: rule match on source text |
| Centred-everything, symmetric card grid, identical section padding, type-scale contrast, overflow | **Rendered**: headless browser DOM geometry and computed styles |
| Squint test, comparison with two or three genre-relevant references from the award set | **Rendered and judged**: screenshots, blind pairing, a scorer other than the author |
| Mobile | A 390 px browser viewport proves responsive web only. A native app claim needs a simulator or device screen, which is outside the pilot; the "mobile app" brief is scored as mobile web and labelled so |
| Better than a competitor | Only against tools run on the same prompts. Freely installable ones are run; paid or sign-in ones (for example the paid Refero MCP) are compared on public documentation and published samples and marked "not run". The no-MCP and current-MCP arms are the primary comparators and need no third party |
| Less convergence | Similarity across the six outputs per arm (shared fonts, palettes, layout skeletons), following the clustering idea in the Boussioux study receipt |

## 6. Constraints (no approval needed)

- **Usage.** Smallest capable model per slice; one author and one reviewer; no new session where an existing one can do it. Per-task token counts are not observable here, so slices are bounded by inputs and attempts: send each worker only the needed evidence and prefer existing sessions. Escalate with the failure log after at most two cheap-tier retries. Write a root cause before retrying beyond three attempts with the same approach. Record tool-visible usage in the ledger where available.
- **Fonts.** Only faces under an open or free-for-commercial licence that load from a public host; the record names the licence. A face whose licence cannot be confirmed is not used.
- **Machine.** Rendering runs under the shared heavy-job lease, one job at a time, and not below 20 GiB free.
- **Rights.** No third-party pixels in the wheel.

## 7. Gaps

- Competitive research covers public workflows, rules, sample artifacts and published studies. Stronger performance claims require controlled runs. Shortlist PyModel for art direction, UI UX Pro Max for rule-driven systems, and a same-host frontend-design skill for prompt scaffolding. Use Refero and Claude Design for published feature comparisons where access requires payment or sign-in. [Market research](research/RESEARCH-COMPETITORS.md)
- The independent review covers the baseline and experiment design. Rendered results still require separate model reviewers and final QA. [Review](evidence/REVIEW.md)
- The "Tyre" book was not found; nothing here cites it.
- The existing suite passed 297 tests and failed the optional-screenshot count test. The rebuild will check packaged imports directly and replace the file-count assertion with checks of available, referenced source evidence. [Baseline test log](evidence/runtime/baseline-pytest.log)
- The award stills are untracked; slice E must re-fetch and hash-match them (`UI-SOURCES.md`).

## 8. Evidence map

| Evidence | Effect |
|---|---|
| AUDIT §2–§3 | Ranking is replaced by authored directions for the new surface; legacy defects with proof get fixed |
| `CONTENT-AUDIT.md` §0; `judged_sample.md`; `REV2-SAMPLE.md` | §3: no deletion, no fixed counts, sources chosen per brief |
| Shin et al. and Boussioux et al. receipts (`market/studies.md`) | Convergence is measured across outputs, not asserted (§5) |
| `RESEARCH-PSYCHOLOGY.md` typicality/novelty; hypothesis caveats | Recognisable skeleton plus one novel decision; strength labels on citations |
| `RESEARCH-CANON.md` closing note | Ratio, tracking and duration ranges are house targets |
| `RESEARCH-TASTE.md` reactions table | `react` implements those four reactions |
| `RESEARCH-USER.md` | Six briefs plus vague prompts; targets are experiment targets, since no user data exists |
| `RESEARCH-UI.md`; `UI-SOURCES.md` | Record fields; three award stills as the benchmark, compared on technique |
| `REFERENCE-MATERIAL.md` | Trackr as a rejection fixture; awards are not quality scores; README screenshot claims dropped when docs are rewritten |

## 9. Acceptance against alternatives

- Give the same host, prompt, brand facts and assets to each runnable MCP or skill arm. Trial PyModel or UI UX Pro Max in the pilot only if it can run without new credentials or charges. Evaluate a plain agent and legacy Design MCP on the full set. Treat hosted products as separate comparisons.
- Check the first call provides one actionable direction and a first-viewport and 390 px reading order. Log the context size and time. Hold the navigation task constant when testing the contribution of art direction. [Study synthesis](research/RESEARCH-WHY-AI-SLOP.md)
- Conceal identifying copy, tool labels and color when testing if the composition distinguishes the six tasks. Check for repeated skeletons and choose a leading direction using the independent written evidence.
- In the full benchmark, target passing first drafts in five of six tasks and all six within two reactions. Use the same rubric for candidate and comparators, report ties and exact sample sizes, and record task completion separately. Use the stronger scope in the competitor gates for any claim against a named product. [Competitive acceptance gates](research/RESEARCH-COMPETITORS.md#beat-them-list)

## 10. Standing development workflow

Use the planner, builder, and independent evaluator roles for subsequent slices. Freeze each slice's acceptance contract and hold out realistic adversarial inputs. Apply the owner's standing design principles to all new designs. Use Playwriter for live browser critique and GPT Computer Use for the final user flow. Apply the blind visual floor and functional checks independently. Revisit the harness and direction catalog as new public research, design examples, and tooling become available. [Design standard](DESIGN-STANDARD.md) · [Design MCP harness](DESIGN-HARNESS.md)

## 11. Rollout after Slice G

1. **Give native GPT Computer Use the first available isolated desktop.** Prepare clean candidate `264cf6c`, which passed all eight macOS 15 install jobs. Verify the installed executable, isolated Chrome profile, extension ID and native host before input. Then go from activation and a toolbar click through the first finding, keyboard Before and After, and reopening the saved preview. Save the OS, build, browser state, timestamps, screenshots and reopened result. Budget 20–30 hands-on minutes once desktop access and native control work. Repeat on the final SHA if it changes. [Install matrix](https://github.com/chrismicah/design-mcp/actions/runs/45000311068) · [Native smoke status](SMOKE-RECEIPTS.md)
2. **Let the existing queues finish the 36-brief benchmark.** Audit the original installs, prompts, assets, model, effort, browser, capture hashes and ballots. The repaired pilot already cleared contrast and interaction checks. Keep repair comparisons separate from the frozen score. Track competitor search coverage separately from generation, and require relevant tool use before scoring a competitor's output. [Benchmark and candidate decisions](EVALS.md) · [Competitor scoreboard](teardown/COMPETITORS.md#visual-scoreboard)
3. **Expand the reviewed catalog from observed gaps.** Default retrieval excludes all 7,080 audited legacy IDs. The pinned snapshot remains available in compatibility mode. The integrated form candidate passes all six routing checks and the return-label rematch. The museum group visit stays provisional for visual acceptance after a tied rematch and a higher earlier control score. Keep the losing pantry candidate on its branch. In its next trial, require distinct time digits, a visible address label and a working keyboard disclosure before blind judging. Use settings cohort results to decide whether to add a settings direction, and verify the saved value and visible controls after reopening. Each direction needs a verified source, version, license, and poor-fit example. Promote after an independent held-out win over the strongest control and a passing primary keyboard task at both widths. [Corpus audit](CONTENT-AUDIT.md) · [Form and pantry evidence](EVALS.md#candidate-decisions)
4. **Test the critique flow on each local input.** Replay a pasted URL, Chrome’s active tab, Electron renderer state and SwiftUI same-window screenshot and Accessibility state. Verify the visible action outcome on the exact build. On the reference Mac, measure 30 cold opens and 30 cold scans. Require p95 of at most 250 ms from toolbar click to a painted, enabled review control and 1 second from that control to the first painted local finding. Track model time separately. [Smoke receipts](SMOKE-RECEIPTS.md) · [Vision approach](research/VISION.md)

Keep full screenshots for release judging. The compact packet saved 14.3% of input tokens against a 40% target. The next single-factor trial uses the cached, masked theatre replay and varies only whether to call the frontier model. Use browser state to identify the remaining room at both widths without inference. Send the full screenshot and region evidence for unresolved hierarchy judgments. Expand a compact packet trial to 12 unseen pairs only after it preserves both judgments and saves at least 40% of input tokens including crops. [Compact vision experiment](EVALS.md#compact-vision-experiment)

Run deterministic checks before each independent live review. Infer reversible defaults and use one build and one calibrated, blind ballot per round. If the held-out dashboard stalls, replace the decorative hero with an exception-first worklist. Stop after two consecutive rounds without improvement once five are scored, or at 15. Retain the strongest build, scores, critique history and screenshots. Release requires at least 9.5 per required screen and separate interaction, privacy and speed passes. [Release rubric](evals/vision/rubric.md)

The hosted checks cover the specific Chrome, Electron, and SwiftUI fixtures. Verify the integrated release on the exact target with GPT Computer Use, from a clean install through activation, first feedback, preview and export or reopen when available. Ventura verification resumes under the shared lease when memory pressure is normal and the Data volume has at least 30 GiB free for guest expansion. [Smoke receipts](SMOKE-RECEIPTS.md) · [Tart evidence](evidence/benchmark-v1/TART.md)
