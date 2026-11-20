# Design MCP ledger

Baseline and fetched `origin/master` both resolved to `82fe6e3749acccf80aecfd523e531be4302865e3`. The workspace branch is `chrismicah/content-quality-audit`. The first section covers work before the product-code approval gate. The audit used light local reads, local probes and public source retrieval, with no paid service or model API calls.

| Lane | Model and session | Token accounting | Proof paths | Review |
| --- | --- | --- | --- | --- |
| Runtime audit and rebuild plan | Claude Fable 5.2, `eb3116f5` | 8k remaining target after owner steering. Actual usage unavailable from the Conductor tools. | [AUDIT.md](AUDIT.md), [PLAN.md](PLAN.md) | GPT-6.2 Sol verified installed stdio and the baseline suite, challenged scope and reviewed the revised plan. [Review](evidence/REVIEW.md) |
| Corpus audit | Claude Opus 5.5, `419b2a67` | 7k remaining target after owner steering. Actual usage unavailable. | [CONTENT-AUDIT.md](CONTENT-AUDIT.md), [content evidence](evidence/content/) | GPT-6.2 Sol requested the removal of source and ID priors, reran the revised score and confirmed corpus coverage. [Review](evidence/REVIEW.md) |
| Model-output and competitor research | GPT-6.2 Astra, `8b478b2c` | 5k remaining target after owner steering. Actual usage unavailable. | [AI design research](research/RESEARCH-WHY-AI-SLOP.md), [competitor research](research/RESEARCH-COMPETITORS.md) | Integrated the documented benchmark shortlist and gates. Live win rates remain unmeasured. |
| Source material, perception, canon, taste, target user and UI | GPT-6.2 Sol, `a33acea8` | Existing primary session. Actual usage unavailable. | [source material audit](evidence/content/REFERENCE-MATERIAL.md), [research](research/), [visual-source receipts](evidence/research/UI-SOURCES.md) | Checked source passages against public evidence, reviewed publisher images, and disclosed indirect evidence and source scope. Fable incorporated the design, taste and user research into the proposed pilot. |
| Product rebuild and adversarial evaluation | Unscheduled | Budget to be set per bounded slice. | [PLAN.md](PLAN.md) | Owner plan approval required before implementation. |

The model targets are spending guidance. Tool access exposes session activity, but no per-task token counter was observed. No additional model session was started after the owner asked to conserve usage.

## Approved rebuild

Owner approved A–G and continuation through the full rebuild on 2026-11-20. This table records the work after approval. Tool-visible token counts remain unavailable.

| Slice | Work and reviewer | Evidence |
| --- | --- | --- |
| A | GPT-6.2 Astra generated two independent six-page source arms. GPT-6.2 Sol captured the required 12 screenshots across the initial three briefs. Fable 5.2 reviewed setup and limits. | [Baseline](evidence/baseline/README.md), `4a9ef28` |
| B | GPT-6.2 Sol authored checks. Fable supplied independent probes for font declaration, color, and copy edge cases. | [Check receipts](evidence/rebuild/design-checks.md), `cbe93b5` |
| C | Claude Opus 5.5 authored six source-backed records. Fable reviewed them and the reusable revision. GPT-6.2 Sol checked palette contrast and fetched font-license receipts. | [Reviewer receipt](evidence/rebuild/pilot-review.md), `ceffdd3` |
| D | GPT-6.2 Sol implemented the MCP tools and compatibility fixes. | [Engine receipt](evidence/rebuild/engine-receipt.json), `5f0808b` |
| E | Existing GPT-6.2 Astra sessions generated the direction and ablated arms after new sessions were refused by Conductor's memory limit. The frozen source checker was replayed across all arms. Candidate renders are held by the resource lease. | [Source comparison](evidence/rebuild/comparison/README.md), `ad7b758` |
| F | GPT-6.2 Sol fixed the held-out routing error, replaced the stale screenshot-count test, and added action evidence to the render harness. Source and stdio checks are green. | [Held-out findings](evidence/rebuild/held-out-findings.md), `0e3953b` |
