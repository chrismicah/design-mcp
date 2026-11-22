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

1. **Give native GPT Computer Use the first available isolated Mac desktop.** The current release proof target is `f17bd6f`. The reference Mac completed the Chrome walkthrough, the Chrome timing series and the SwiftUI and Electron Reveal interactions. Repeat affected checks when the package changes. [Install matrix](evidence/benchmark-v1/direct-git-install-f17bd6f.json) · [Native smoke status](SMOKE-RECEIPTS.md)
2. **Use the frozen 36-brief benchmark as the reference.** Design MCP scored 94.1 and plain generation scored 92.7. The paired bootstrap interval crosses zero. Keep repair comparisons outside the frozen score. A competitor visual result requires relevant tool use, matched conditions and an anonymous ballot. Scope each claim to the tested briefs, count ties separately, and track retrieval coverage and token usage independently. An overall ranking requires a representative common set for the named competitors. [Benchmark](EVALS.md) · [Competitor scoreboard](teardown/COMPETITORS.md#visual-scoreboard)
3. **Expand the reviewed catalog from observed gaps.** Default retrieval excludes all 7,080 audited legacy IDs. The pinned snapshot remains available in compatibility mode. The integrated form candidate passes all six routing checks and the return-label rematch. The museum group visit stays provisional for visual acceptance after a tied rematch and a higher earlier control score. For the settings candidate, require the actual `surface=form` trace to select the intended direction, then use hosted Playwriter to save a fresh value and verify it and the visible controls after reopening at both widths. This can proceed while the host desktop is occupied. Each direction needs a verified source, version, license, and poor-fit example. Promote after an independent held-out win over the strongest control and a passing primary keyboard task at both widths. [Corpus audit](CONTENT-AUDIT.md) · [Candidate evidence](EVALS.md#candidate-decisions)
4. **Test the critique flow on each local input.** Replay a pasted URL, Chrome’s active tab, Electron renderer state and SwiftUI same-window screenshot and Accessibility state. Verify the visible action outcome on the exact build. On the reference Mac, measure 30 cold opens and 30 cold scans. Require p95 of at most 250 ms from toolbar click to a painted, enabled review control and 1 second from that control to the first painted local finding. Track model time separately. [Smoke receipts](SMOKE-RECEIPTS.md) · [Vision approach](research/VISION.md)

Keep `collection-details` experimental after three real pantry calls selected the transit direction. Reopen automatic selection when a catalog selection change can pass the three archived stdio calls, an unseen appointment brief through the public tool, exclusions for public schedules, slot selection and staff boards, and parity on the other 35 frozen briefs. Then run one unhinted matched generation and require the actual reply to select `collection-details` before rendering. At 1440 and 390 pixels, check distinct time digits, a visible address label, and keyboard disclosure and collapse with retained focus. Require a blind win over the stronger plain control before promotion. Label any manually selected direction as a design experiment. [Pantry routing evidence](EVALS.md#candidate-decisions)

Test an optional `task_intent` in the existing `direct` call after both empty-state generations missed the candidate’s phrase rules. A client chooses a primary action only when it can infer it from the brief. The first two intents cover trying a suggested query and reserving the first volunteer shift. Preserve the tool description, existing fields and defaults, and exact text and structured replies for omitted and null intent. Preserve fallback replies for incompatible surfaces and excluded records. [Stdio evidence](evidence/benchmark-v1/explicit-task-intent-source.json)

Run the two unseen positive probes before the four lookalikes. Require the right intent and direction ID on both positives, zero specialist selections on the four lookalikes, and one unhinted tool call per probe. Read the raw trace to distinguish schema registration, caller selection, routing, and evaluator failures. If a correct typed replay works but a client overlooks or misuses the visible field, revise its description once and use fresh holdouts. A second discovery miss keeps the feature experimental. After all six probes pass, run fresh matched full generations with the original schema on the integrated parent. Require the intended direction on the first candidate call before rendering. Each family earns promotion with a passing keyboard action at 1440 and 390 px and an independent blind win over its strongest control. Keep this experiment outside the frozen 36. [Benchmark routing gate](evals/v1/README.md)

Both optional-intent directions passed routing and lost the first live comparison. Pause expansion of the enum until the design work earns a win. Preserve the old-schema controls as the visual reference for this repair. In search, keep the result illustration and make clearing remove the stale match immediately. In booking, keep the visible offer label and emphasize when the shift starts and ends. Focus the actual booked record so it reads as a confirmation. Use a compact Playwriter interaction surface for the next blind trial and measure its total and uncached input against the first trial. [Live verdict and critique](evidence/benchmark-v1/explicit-task-intent-live-ballot.json)

Keep full screenshots for release judging. The compact packet saved 14.3% of input tokens against a 40% target. The cached theatre replay answered which room remained at both widths without inference and withheld an answer in six contradictory or incomplete cases. Extend this dispatch check to unseen routine findings. Use the full screenshot and region evidence for unresolved hierarchy judgments. Expand a compact packet trial to 12 unseen pairs only after it preserves both judgments and saves at least 40% of input tokens including crops. [Compact vision experiment](EVALS.md#compact-vision-experiment)

Run deterministic checks before each independent live review. Infer reversible defaults and use one build and one calibrated, blind ballot per round. If the held-out dashboard stalls, replace the decorative hero with an exception-first worklist. Stop after two consecutive rounds without improvement once five are scored, or at 15. Retain the strongest build, scores, critique history and screenshots. Release requires at least 9.5 per required screen and separate interaction, privacy and speed passes. [Release rubric](evals/vision/rubric.md)

The hosted checks cover the specific Chrome, Electron, and SwiftUI fixtures. Verify the integrated release on the exact target with GPT Computer Use, from a clean install through activation, first feedback, preview and export or reopen when available. Ventura verification resumes under the shared lease when memory pressure is normal and the Data volume has at least 30 GiB free for guest expansion. [Smoke receipts](SMOKE-RECEIPTS.md) · [Tart evidence](evidence/benchmark-v1/TART.md)

## 12. Release proof and next held-out comparison

- The `f17bd6f` package passed the eight-job macOS 15 install matrix and the hosted Chrome toolbar check. GPT Computer Use then recovered the missing host locally, showed the first finding, switched Before and After by keyboard, and reopened the masked preview. The reference Mac still needs 30 cold opens and 30 cold scans against the 250 ms and 1 second p95 gates. [Native smoke receipts](SMOKE-RECEIPTS.md)
- Keep the 56% Ventura image and checksummed bundle. Allow 1–3 hours for the Apple Silicon guest after the shared lease and disk headroom are available. Intel Ventura requires its own runtime evidence. Repeat the relevant install and smoke checks if the shipping build changes. [Tart evidence](evidence/benchmark-v1/TART.md)
- Preregister one unseen catalog search with no exact result and an in-stock substitute. Change one `direct` instruction to place the substitute's name and stock count on its action. Use one unhinted MCP call per arm and fix the prompt, schema, model, assets, and budget across arms. Verify selection, immediate query clearing, focus, and no stale match at 1440 and 390 px. Run the standing live critique cycle with the strongest verified revision retained. Direction promotion requires a blind win and at least 9.5 on every required view. Budget 1–5 hours for this study. Keep both optional intent routes experimental and leave the 36 frozen pairs intact. The release comparison still requires a representative common set across competitors. [Benchmark](EVALS.md) · [Competitor scoreboard](teardown/COMPETITORS.md#visual-scoreboard)
- Return local review immediately using masked evidence, roles, bounds, and observed interaction outcomes from Playwriter, the Electron renderer, or Swift Accessibility. Send one bounded frontier vision request when the local evidence cannot resolve a finding. Use original frames for hierarchy judgments and release ballots. Before expanding, compare identical cases and require matching judgments, at least 40% fewer total input tokens including escalations, and no masking or interaction regressions. Include the overlapping and clipped Electron controls and the Swift Reveal action. Allow 1–3 hours for initial qualification. [Vision research](research/VISION.md)
- Use the weekly source watcher to queue verified, licensed candidates. The planner defines the user outcome and holds out test cases. The builder runs deterministic checks first. Independent live review decides which candidates earn promotion. Test one harness simplification at a time against the same cases, measuring quality, time, and input tokens. [Design MCP harness](DESIGN-HARNESS.md)

## 13. Simulated non-designer pilot

Run `dashboard/clear` and `pricing/misleading` from the sealed 24-case prompt set. Pair the plain generator with the verified `2fcd312` package. Use fresh sessions with the same model, client, assets, budget and stripped project brief. Give each session the exact first prompt. Keep the rubric and later reactions out of its context until needed. Record each recommended answer and count a third question as a miss. After a missed render, send the next sealed reaction. Stop at the first pass or after two reactions. Include timeouts in the denominator. [Prompt set and protocol](evals/reactions/README.md)

An independent Playwriter reviewer receives randomized arm labels, exercises the main action at 1440 and 390 px, and checks focus, reflow, and supplied facts. Record steps, time to first pass, token usage, and blind preference. Allocate 60–120 active minutes for four initial drafts and up to eight revisions. Expand to the remaining 22 unchanged cases if the clear candidate passes on the first attempt, both candidates earn at least 9.5 on every required view within two reactions, and the candidate wins at least one blind comparison while taking no more steps on either. Keep this simulated-user evidence separate from the frozen 36 and from competitor rankings. [Standing design standard](DESIGN-STANDARD.md)

### Next blind review

Both pilot cases finished. Zero of two Design MCP cases reached 9.5 at both widths on the first draft or after two reactions. Keep the 22 remaining cases sealed and use separate held-out briefs to test repairs. The standing live acceptance loop still applies to release candidates. [Pilot results](EVALS.md#simulated-non-designer-pilot)

The first reaction's blind ballot favored Design MCP at both widths and its scores fell 0.05 from the initial ballot at each width. The second reaction recovered both scores and yielded the strongest Design MCP dashboard in the pilot. It kept the next deadline visible and restored focus, with the reversal control still below the manifest. Carry forward the deadline and focus behavior. Test the in-place reversal and tighter ID–delay grouping on the held-out cold-storage comparison. [First reaction ballot](evidence/benchmark-v1/reaction-pilot-dashboard-calmer-live.json) · [Final dashboard ballot](evidence/benchmark-v1/reaction-pilot-dashboard-too-generic-live.json)

The second reaction also produced the strongest Design MCP pricing draft, at 9.00 desktop and 8.90 mobile. Preserve its visible prices and allowances, keyboard selection, and focus return. A future pricing repair should make the selected tier name visually distinct on desktop and strengthen the chart connectors on mobile. [Final pricing ballot](evidence/benchmark-v1/reaction-pilot-pricing-too-generic-live.json)

Keep the exception focus changes at `b9e4bd6` experimental. Test the held-out cold-storage brief with the stock and revised directions on the same fixed router, with plain generation as a reference. Verify the returned direction, then check that the supplied ID leads, the reversal stays in place, and the next deadline stays visible at both widths before a blind live comparison. Keep these results outside the frozen scoreboard. [Stdio parity and candidate pin](evidence/benchmark-v1/exception-focus-repair-parity.json)

The hosted keyboard replay verifies the dashboard revisions. GPT Computer Use completed the toolbar-to-preview flow on `f17bd6f` and saved the reopened state. [Native and hosted smoke status](SMOKE-RECEIPTS.md)

## 14. Next quality comparison

GPT-6.2 Astra ranked the experiments below after reviewing the frozen benchmark, reaction pilot, and routing audit. The benchmark remains 94.1 for Design MCP and 92.7 for plain generation across 36 pairs, with a confidence interval that crosses zero. [Astra planning session](conductor://workspace?id=74a3d728-740d-4ccc-af7a-eb3ceb641950&session=1368f377-804a-40f3-a69e-122f71853fee) · [Benchmark](EVALS.md)

1. **Run the held-out cold-storage comparison first.** Use the same corrected router for the stock and revised directions, with plain generation as the reference. Pin the prompt, generator, effort, asset policy and budget. Require `exception-first` on the first unhinted call in both MCP arms before rendering. Keep the frozen routing replies and the landing lookalike as source controls. At 1440 and 390 px, require the supplied ID to lead beside its delay, the reversal control to stay in place, the next deadline to stay visible, and keyboard reversal to restore all rows and return focus. A separate calibrated critic exercises the anonymized builds and a withheld recovery case before scoring. A strict win over the strongest control at each width earns the next round. A tie, loss or behavioral miss leaves the repair experimental. Launch when the full comparison fits the observed quota above the reserve. [Routing diagnosis](evidence/benchmark-v1/current-direct-routing-diagnostic.json) · [Pinned comparison](evidence/benchmark-v1/exception-focus-repair-parity.json)
2. **Run the matched shadcn maintenance form next.** Reuse the archived control only with matching generator, shell policy, Chrome and Playwriter. Require a successful, relevant shadcn 4.23.0 component retrieval in the generation trace before rendering. The independent evaluator checks keyboard validation, confirmation, editing and focus at both widths. Report the blind result for this form. [Registry evidence and scoreboard](teardown/COMPETITORS.md#visual-scoreboard)
3. **Test a cheaper focus diagnosis on the same cold-storage interactions.** Compare full-frame evidence with masked browser DOM and accessibility observations plus one scoped screenshot. Keep the action and question fixed. Escalate ambiguous observations to the original frame and count its input tokens. Expand this route only if answers and abstentions match, masking and interaction checks pass, and total input drops at least 40%. The independent visual ballot still uses original full-resolution frames. [Prior focus replay](evidence/benchmark-v1/frontier-focus-return-replay.json) · [Live review rubric](evals/vision/rubric.md)

The pilot expansion and release requirements apply separately. Keep the remaining 22 prompts sealed and the 36 frozen pairs intact. [Pilot outcome](EVALS.md#simulated-non-designer-pilot)

Use a real pointer press on the pinned Chrome toolbar button for the reference-Mac timing trials. Start the open timer at that press and stop when the Scan control is actionable. Time Scan through the visible finding separately. Record every attempt and report p95 only if all 30 samples complete. Keep the hosted keyboard result as diagnostic evidence. [Hosted timings and timeout receipts](evidence/benchmark-v1/chrome-first-activation-mac.json)

## 15. Native smoke when the browser bridge is unavailable

GPT-6.2 Astra set a five-minute capability probe for the first staged desktop with confirmed input ownership. Start with the seeded shuttle fixture in a disposable Chrome profile. Verify the profile path, focused fixture window, installed `f17bd6f` extension and profile-scoped native host. Recheck the browser bridge once with Chrome running. If the bridge is unavailable and GPT Computer Use exposes the identified Chrome window as a controllable native app, use it to click the pinned toolbar button once. Save the bridge status, action receipt, and before and after evidence from that window. The probe passes when Scan appears enabled after the click. [Astra decision](conductor://workspace?id=74a3d728-740d-4ccc-af7a-eb3ceb641950&session=1368f377-804a-40f3-a69e-122f71853fee) · [Exact candidate install matrix](evidence/benchmark-v1/direct-git-install-f17bd6f.json)

The reference Mac walkthrough passed on installed Chrome 157. The browser bridge remained unavailable after launch. GPT Computer Use drove the isolated Chrome window through its native accessibility tree and keyboard, including extension setup, the 2.6-to-1 finding, After and reopening the masked file on Before. Use this route again when the bridge is unavailable and the owned browser profile and window identity can be verified. Preserve the last observed state if input stops reaching the named window. [Reference Mac receipt](evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

With `f17bd6f`, a custom host stores reviews inside its own Chrome data directory. The candidate passed the hosted Linux and macOS toolbar flows and all eight macOS 15 install jobs. The original staged `2fcd312` local install serves as the historical control. [Profile isolation receipt](evidence/benchmark-v1/chrome-profile-review-isolation.json)

### Remaining release checks

GPT-6.2 Astra reviewed the local and hosted receipts and prioritized Electron before Chrome timing. The reference Mac completed the Electron walkthrough. The native Chrome result above establishes a working route when the browser bridge is unavailable. [Astra planning session](conductor://workspace?id=74a3d728-740d-4ccc-af7a-eb3ceb641950&session=1368f377-804a-40f3-a69e-122f71853fee)

1. **Electron.** Stage the official Electron 43.4.0 arm64 archive under the shared lease and verify its pinned digest and app signature. Record the harness revision and verify the existing automated mode. With the owned app staged, run with `DESIGN_MCP_ELECTRON_MANUAL_INPUT=1` and wait for the initial capture. Use GPT Computer Use to focus “Reveal control” and press Return in that window. Require the native action receipt, visible change, and hashed before and after exports reviewed by the installed `f17bd6f` CLI. Both captures must contain four controls at 880 × 640. The `control-not-hittable` finding for `r2` must clear and `control-clipped` for `r4` must persist. Stop on target mismatch or after the harness's 120-second wait. [Expected fixture findings](evidence/benchmark-v1/reference-mac-desktop-f17bd6f.json)
   - Complete for the current reference Mac fixture. The separate development app passed signature verification under its dedicated bundle ID. GPT Computer Use completed Tab and Return successfully after the harness began validating the Retina image separately from the CSS viewport. The CLI replay, Accessibility state and original screenshots agreed. [Fixture recipe](evals/vision/package_electron_fixture.sh) · [Local receipt](evidence/benchmark-v1/reference-mac-electron-f17bd6f.json)
2. **Chrome timing.** Keep eager collection. The reference Mac completed all 30 closed-to-open pointer trials in the running browser. The p95 of 136 ms to the actionable Scan state and 100 ms from Scan to the first finding met the 250 ms and 1 second targets. Preserve the native event timestamps, Accessibility observations, and mask check with the receipt. Hosted launches from fresh profiles have separate timings. [Reference Mac timing receipt](evidence/benchmark-v1/chrome-reference-latency-f17bd6f.json)
3. **Ventura.** Resume the pinned Apple Silicon guest pull under the shared lease at 30 GiB free with normal memory pressure. Run both installers and the MCP smoke in the booted Ventura guest. Obtain separate Intel Ventura runtime evidence. [Ventura evidence](evidence/benchmark-v1/TART.md)
4. **Blind comparison.** Launch cold storage when generation and live judging fit above the subscription reserve. The local preflight reproduced equal tool schemas, the expected routes, and only the two intended changes in the revised direction. Apply the trace, keyboard, recovery and strict blind-win checks in §14. An eligible release design reaches at least 9.5 at both widths. Follow the standing rule to stop after two consecutive non-improvements once five rounds are scored, or at round 15. The matched shadcn form follows cold storage. [Direction parity](evidence/benchmark-v1/exception-focus-repair-parity.json) · [Release rubric](evals/vision/rubric.md)
