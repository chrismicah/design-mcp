# Design MCP ledger

Baseline and fetched `origin/master` both resolved to `82fe6e3749acccf80aecfd523e531be4302865e3`. The workspace branch is `chrismicah/content-quality-audit`. All work in this ledger is before the product-code approval gate. The audit used light local reads, local probes and public source retrieval, with no paid service or model API calls.

| Lane | Model and session | Token accounting | Proof paths | Review |
| --- | --- | --- | --- | --- |
| Runtime audit and rebuild plan | Claude Fable 5.2, `eb3116f5` | 8k remaining target after owner steering. Actual usage unavailable from the Conductor tools. | [AUDIT.md](AUDIT.md), [PLAN.md](PLAN.md) | GPT-6.2 Sol verified installed stdio and the baseline suite, challenged scope and reviewed the revised plan. [Review](evidence/REVIEW.md) |
| Corpus audit | Claude Opus 5.5, `419b2a67` | 7k remaining target after owner steering. Actual usage unavailable. | [CONTENT-AUDIT.md](CONTENT-AUDIT.md), [content evidence](evidence/content/) | GPT-6.2 Sol requested the removal of source and ID priors, reran the revised score and confirmed corpus coverage. [Review](evidence/REVIEW.md) |
| Model-output and competitor research | GPT-6.2 Astra, `8b478b2c` | 5k remaining target after owner steering. Actual usage unavailable. | [AI design research](research/RESEARCH-WHY-AI-SLOP.md), [competitor research](research/RESEARCH-COMPETITORS.md) | Integrated the documented benchmark shortlist and gates. Live win rates remain unmeasured. |
| Source material, perception, canon, taste, target user and UI | GPT-6.2 Sol, `a33acea8` | Existing primary session. Actual usage unavailable. | [source material audit](evidence/content/REFERENCE-MATERIAL.md), [research](research/), [visual-source receipts](evidence/research/UI-SOURCES.md) | Checked source passages against public evidence, reviewed publisher images, and disclosed indirect evidence and source scope. Fable incorporated the design, taste and user research into the proposed pilot. |
| Product rebuild and adversarial evaluation | Unscheduled | Budget to be set per bounded slice. | [PLAN.md](PLAN.md) | Owner plan approval required before implementation. |

The model targets are spending guidance. Tool access exposes session activity, but no per-task token counter was observed. No additional model session was started after the owner asked to conserve usage.
