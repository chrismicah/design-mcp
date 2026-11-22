# Rebuild status

Owner approval is recorded in [PLAN.md](../../PLAN.md). The active product line is `design-mcp/f-held-out-fixes`.

| Slice | Branch | Receipt |
| --- | --- | --- |
| A | `design-mcp/a-baseline` | 12 source outputs, frozen checker hash, 12 1440/390 captures across three briefs. [Baseline](../baseline/README.md) |
| B | `design-mcp/b-design-checks` | Static rule fixtures pass. [Check log](checks-pytest.log) |
| C | `design-mcp/c-reviewed-directions` | Six validated direction records, two independent review passes and 11 font license receipts. [Final review](pilot-review.md) |
| D | `design-mcp/d-engine` | Three new calls, 14 compatible tool names, compact payloads, palette generation moved inside the package. [Engine receipt](engine-receipt.json) |
| E | `design-mcp/e-ablation` | Sources and frozen tell checks complete. Playwriter verified 24 primary keyboard actions. Blind ballots are recorded for the three pilot briefs. [Comparison](comparison/README.md) |
| F | `design-mcp/f-held-out-fixes` | Fixed a held-out operations-board route, stale screenshot test, font loading, and three primary controls. 307 tests pass. [Results](suite.log) · [Source challenge](challenge-response.md) |
| F live smoke | `52540b5` | Fixed Codex approval blocking the v2 tools. Codex called `direct`, produced a theatre board, and GPT Computer Use verified the filter and restore at desktop width and 390 px. [Live proof](../../SMOKE-RECEIPTS.md) |
| F theatre follow-up | `design-mcp/f-held-out-fixes` | The owner rejected both visual drafts. The stage call sheet reference passed desktop and 390 px interaction checks. Visual acceptance remains open. [Revision](live-smoke/theatre-revision.md) |
| G | Repair and rerun | The full direction lost the coffee and train comparisons. The repair branch revises the two direction records, pending matched verification. [Decision](comparison/README.md#slice-g-decision) |

The direction arm had 0 static findings across six briefs, compared with 8 in N and 7 in L. The ablated arm had 0 across three. Static score improvement shows the implemented rules caught fewer tells in the source outputs. Visual preference, task success and the value of rationale and citations require rendered comparison.

The Mac shared-resource lease refused candidate rendering on 2026-11-20. The first refusal recorded `free_gib: 20.1`, `pressure: 2`, and `allowed: false`. The final check after live smoke still reported level 2 with 30.34 GiB free. Conductor declined a new Astra session. The two candidate arms were generated in existing sessions, which introduced prior-arm exposure. [Lease receipt](e-render-resource.log)

Independent Astra reviewers scored the randomized screenshots under the frozen rubric. Coffee and train repairs now need fresh matched verification. Corpus culling and source rewrites for broad rollout follow the verified comparison. The expanded challenge suite, fresh install, and computer-use smoke remain open. [Hosted browser evidence](comparison/hosted-pilot-browser.json)
