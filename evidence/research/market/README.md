# Market research proof index

Collected 20 November 2026 for the Design MCP audit. This lane used anonymous public HTTP GETs, local text and data inspection, and inspection of publisher-supplied examples. All claims about a competitor’s usual output remain open unless a study specifies a population. No product was installed or exercised. No interactive UI, authenticated requests, external model runs or purchases were used for the research.

| Proof | What can be checked |
|---|---|
| [Studies](studies.md) | S1 verifies the abstract, PDF masthead and full paper. S2 follows a forward citation into a measured web-design cohort. S3–S10 record corroboration, alternative explanations and limits. Each receipt identifies the source, locator, retrieval time and response digest. |
| [Product sources](products.md) | Nine shortlist receipts cover tool contracts, public examples, source links and response digests. For the Meridian still the digest covers the public image. |
| [Market search](discovery.json) | All 24 search requests, request URLs, UTC times, status codes, response digests and ranked identifiers. Search positions and distinct identifiers are counted separately for each service. |
| [UI UX Pro Max source counts](pro-max-rule-counts.json) | Commit-pinned CSV URL, body digest, counting method, two exact pattern counts, blank-reasoning total and selected general SaaS row fields. |
| [Why generated UIs converge](../../../research/RESEARCH-WHY-AI-SLOP.md) | Interpretation, counterevidence and proposed controlled tests. |
| [Competitor teardown](../../../research/RESEARCH-COMPETITORS.md) | Six direct MCP competitors, three adjacent benchmarks, sample judgments, unresolved questions and comparative acceptance criteria. |

## Local baseline

Checked commit `82fe6e3749acccf80aecfd523e531be4302865e3`. The installed console entry maps to `design_mcp.cli:main` in [pyproject.toml](../../../pyproject.toml). The serve path imports the packaged server at [design_mcp/cli.py](../../../design_mcp/cli.py#L32). The following are static source observations.

| Source | Observation | Git blob at inspected commit |
|---|---|---|
| [Packaged pattern search](../../../design_mcp/database.py#L51) | Filters precede query scoring. Each whitespace-separated term earns one point for a substring match in joined fields. Descending stored quality breaks ties; the no-query branch sorts by quality. | `c27980475e933f25cb6106456879603cb02b652a` |
| [Packaged tool](../../../design_mcp/server.py#L86) | Search defaults to web and five results, converts each result to a blueprint and optionally projects fields. | `80c20c4366ff6e89e402f11e34eea385d82197cf` |
| [Packaged design-system tool](../../../design_mcp/server.py#L475) | The default arguments are Dashboard and dark. The tool reads shared font and spacing systems and accepts a named aesthetic. This is a second possible source of repeated choices. | `80c20c4366ff6e89e402f11e34eea385d82197cf` |

## Scope and ledger handoff

Author: Codex, GPT-6-based research session. Initial budget target: 16,000 tokens. Owner requested a compact follow-up targeting about 5,000 additional tokens. Actual billable usage: unavailable. Independent review: pending coordinator assignment. No measured competitive win. Static research is complete for these two reports; proposed paired tests require a separately authorized QA lane.

The registry search for “design” consumed its full cursor chain (229 names). npm and GitHub searches are ranked slices and other registry queries are bounded. Exclusions include software architecture patterns, printing, industrial design, astrology, generic package dependencies and unrelated services containing a search term. Records preserve these false positives. The package, repository and registry identifiers for one product can differ. Cross-channel counts are consequently kept separate.

Search for the follow-up study used OpenAlex’s works linked by citation to the seed, then the author’s versioned arXiv full text and the Crossref/SSRN abstract. A direct SSRN page returned HTTP 403; both the public author text and publisher-deposited abstract were accessible. [Forward citation query](https://api.openalex.org/works?filter=cites%3AW7136244561) · [Full-text receipt](studies.md#s2)
