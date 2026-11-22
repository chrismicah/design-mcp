# Design acceptance with short reactions

This suite uses six existing project briefs and four short user prompts per brief. It tests how quickly a non-designer can use plain language to get a usable, distinctive first draft, then ask for a narrow change. The 24 prompt cases belong to a separate benchmark series. [Target user and acceptance rationale](../../research/RESEARCH-USER.md#acceptance-experiment)

## Run the same conversation in each arm

1. Verify the source brief file against the hash in `tasks.json`. Remove the source brief's leading style request by splitting once at the first period followed by a space. Give each generator the remaining text as project context and one exact user prompt from the case. Use the same model, client, asset policy, and time budget in both arms.
2. Log any question verbatim and take its recommended answer when one is available. Record each answered question, tool call, rendering time, and model usage separately. Answer at most two questions and record any excess as a failure.
3. A separate blind reviewer opens the build, attempts the stated action at 1440 and 390 CSS px, and checks focus, reflow, and the visible result. Save original captures, a squint view, the static tell check, and comparisons with two or three relevant award examples. Use the standing weighted rubric on every required screen. [Live rubric](../vision/rubric.md)
4. If the first build misses, send the next exact reaction from `tasks.json`. In the candidate arm the client may call `react`. The control receives the same words and timing rule. Reopen the revised build, verify the primary action and protected facts, and record the changes the user can actually see. Stop on the first pass or after the two supplied reactions.
5. Report clear first-pass rate, time to first pass, steps per case, percentage passing within two reactions, and paired blind preference. Include misses and timeouts in the denominator. This is a simulated-user experiment.

For a revised version of this suite, record changed prompts, response rules, preserved facts, and the reason before launching a comparison. Keep the original prompts and results readable.

## Start the two-pair pilot

Use the verified `2fcd312` install kit and an authenticated subscription client. The runner opens two fresh sessions per case, checks the quota before each pair, and writes the prompt, JSONL trace, thread ID, and HTML digest under a new output directory. The saved thread ID lets the operator send the next exact reaction to that generator after review. Inspect any `review-reply` before responding. Record a genuine question and its recommended answer, or count an invalid draft as a miss. A timed-out cell stays in the record.

```sh
python3 evals/reactions/pilot.py --out "$PILOT_OUTPUT" --kit "$VERIFIED_INSTALL_KIT" \
  --quota-probe "$SUBSCRIPTION_QUOTA_PROBE" --model "$GENERATOR_MODEL"
```

Give the reviewer anonymous fixtures after checking the HTML and trace digests against the receipts. Keep the thread IDs, arm mapping and generator replies out of the review. Use original browser captures for acceptance. [Browser review setup](../v1/README.md#compact-live-review) · [Pilot cases and gates](../../PLAN.md#13-simulated-non-designer-pilot)

The live runner checks that both drafts used the same prompt, client, model, effort and reaction round. It serves them in isolated browser origins with randomized labels, then starts one independent critic with access only to the browser review tools. Keep the output directory private until the ballot is saved.

```sh
python3 evals/reactions/live_review.py --cells "$PILOT_OUTPUT" \
  --case dashboard-clear --out "$LIVE_REVIEW" --model "$CRITIC_MODEL" \
  --chrome "$CHROME_EXECUTABLE" --playwriter "$PLAYWRITER_EXECUTABLE" \
  --quota-probe "$SUBSCRIPTION_QUOTA_PROBE"
```

After the critic submits a ballot, audit the anonymous run against the generation receipts. The audit checks independence, activation and recovery inputs, and that each PNG sent to the critic matches the archived file. Keep missing scores visible in the denominator. Check the observed task outcomes against the browser audit before recording a pass.

```sh
python3 evals/reactions/audit_review.py --run "$LIVE_REVIEW" --cells "$PILOT_OUTPUT" --case dashboard-clear
```

Save the audited ballot as JSON before resuming either arm. The follow-up runner uses the original client version, package pin, and thread. It checks both viewport scores against the same draft and selects the next reaction from the sealed case.

```sh
python3 evals/reactions/follow_up.py --case dashboard-clear --arm design-mcp \
  --previous "$PILOT_OUTPUT/dashboard-clear/design-mcp" --ballot "$AUDITED_BALLOT" \
  --out "$NEXT_ROUND/dashboard-clear/design-mcp" --kit "$VERIFIED_INSTALL_KIT" \
  --scratch "$PILOT_OUTPUT/empty-client-workspace" --quota-probe "$SUBSCRIPTION_QUOTA_PROBE"
```

## Review a held-out benchmark

For the cold-storage and shadcn maintenance studies, use a separate benchmark specification with `case`, the exact generation `brief`, the independent critic's `task`, and two or three `arms` matching the cell directories. A `directions` map pins the expected first MCP replies, and `browser` can pin the Chrome version of an archived control. Keep the specification with the evaluator and give the generator only the generation brief.

```sh
python3 evals/reactions/live_review.py --cells "$BENCHMARK_CELLS" \
  --benchmark-spec "$BENCHMARK_SPEC" --check-input
```

The preflight replays the traces and verifies distinct generator sessions, prompt and HTML hashes, and matching generator and shell settings. In the cold-storage spec, set `require_unhinted_direct` to `true` and declare the expected direction for each Design MCP arm. The preflight then verifies that the exact generation brief was the sole argument of the arm's only tool call. The shadcn arm must contain the registry evidence declared in its benchmark configuration. Use the same options with the live runner above, passing `--benchmark-spec` in place of `--case` and dropping `--check-input`. The audit takes the same specification and requires an original-image live ballot for both widths of every arm. [Benchmark plan](../../PLAN.md#14-next-quality-comparison)

For the held-out dispatch journey, enable `require_cold_storage_journey` and keep `journey_facts` in the private benchmark spec. It contains the five `ids` in order, the `id_pattern`, patterns for `delay` and `deadline`, and one list of required `facts` patterns for each load. Capture `before`, `focused` and `after` for each anonymous viewport. The local audit records rendered text, in-viewport text, scroll position, and a hit test at the invoking control's original center. It checks the keyboard states immediately before and after activation and reversal. It returns the behavior result beside the critic's independent score for each screen. A recorded failure stays in the ballot. Missing or interrupted evidence invalidates the affected ballot. The critic still checks readability, visual grouping and the recovery in the live build.
