# Rebuild status

Owner approval is recorded in [PLAN.md](../../PLAN.md). The active product line is `design-mcp/f-held-out-fixes`.

| Slice | Branch | Receipt |
| --- | --- | --- |
| A | `design-mcp/a-baseline` | 12 source outputs, frozen checker hash, 12 1440/390 captures across three briefs. [Baseline](../baseline/README.md) |
| B | `design-mcp/b-design-checks` | Static rule fixtures pass. [Check log](checks-pytest.log) |
| C | `design-mcp/c-reviewed-directions` | Six validated direction records, two independent review passes and 11 font license receipts. [Final review](pilot-review.md) |
| D | `design-mcp/d-engine` | Three new calls, 14 compatible tool names, compact payloads, palette generation moved inside the package. [Engine receipt](engine-receipt.json) |
| E | `design-mcp/e-ablation` | Sources and frozen tell checks complete. Candidate screenshots and independent paired scores remain pending. [Comparison](comparison/README.md) |
| F | `design-mcp/f-held-out-fixes` | Fixed a held-out operations-board route, stale screenshot test, font loading, and three primary controls. 307 tests pass. [Results](suite.log) · [Source challenge](challenge-response.md) |
| F live smoke | `52540b5` | Fixed Codex approval blocking the v2 tools. Codex called `direct`, produced a theatre board, and GPT Computer Use verified the filter and restore at desktop width and 390 px. [Live proof](../../SMOKE-RECEIPTS.md) |
| F theatre follow-up | `design-mcp/f-held-out-fixes` | The owner rejected the initial visuals. Theatre briefs now get a stage call sheet instead of the dispatch layout. The reference implementation passed desktop and 390 px interaction checks. [Revision](live-smoke/theatre-revision.md) |
| G | Pending | Compare control and direction screenshots and check task completion before using the results to expand. |

The direction arm had 0 static findings across six briefs, compared with 8 in N and 7 in L. The ablated arm had 0 across three. Static score improvement shows the implemented rules caught fewer tells in the source outputs. Visual preference, task success and the value of rationale and citations require rendered comparison.

The Mac shared-resource lease refused candidate rendering on 2026-11-20. The first refusal recorded `free_gib: 20.1`, `pressure: 2`, and `allowed: false`. The final check after live smoke still reported level 2 with 30.34 GiB free. Conductor declined a new Astra session. The two candidate arms were generated in existing sessions, which introduced prior-arm exposure. [Lease receipt](e-render-resource.log)

Once the lease admits work, render both candidate arms at 1440 and 390, run the keyboard action check, create randomized screenshot pairs, and have the Fable coordinator apply the frozen rubric. The next rollout decision depends on those results. The cull, source rewrites, expanded challenge suite, fresh install, and computer-use smoke test follow the verified comparison and any necessary fixes.
