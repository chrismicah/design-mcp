# Changelog

## Unreleased

- Added the 36-brief matched benchmark with clean-session token accounting, Playwriter captures, blind judging, and competitor adapters. The first fifteen judged briefs averaged 91.9 without the MCP and 94.4 with it. [Benchmark](EVALS.md)
- Added `design-mcp doctor`, offline directions, and lazy loading of the checksum-verified legacy corpus. Fresh pipx and uv installs exercised all 17 tools with Python 3.10–3.13 on both Intel and Apple Silicon macOS 15. The client examples use the installed command. [Install results](EVALS.md#candidate-decisions)
- Tested four credential-free design tools over stdio. In the first matched browser comparison, hosted Inspo scored 87.5 on ceramics and Design MCP scored 91.7. [Competitor results](teardown/COMPETITORS.md#visual-scoreboard)
- Measured compact computer-vision context against full-size screenshots and specified a fast local first review before frontier vision. [Vision research](research/VISION.md)
- Made the planner, builder, and independent evaluator workflow standard. Added recurring public source discovery and connected the visual release verdict to the exact browser captures. [Development harness](DESIGN-HARNESS.md)
- Added separate radio and service-booking directions. Both improved on the frozen v2 in their matched blind comparisons and passed keyboard task checks at desktop and mobile widths. [Visual and interaction results](EVALS.md#candidate-decisions)
- Updated the product direction to put price, shipping and the purchase action together on narrow screens. The ceramics comparison improved from 87.5 to 95.8 and its keyboard purchase passed at both widths. [Matched receipts](evidence/benchmark-v1/product-hero-visual.json)

The form-routing branch remains a candidate. Visual acceptance is tracked in the benchmark. [Candidate decisions](EVALS.md#candidate-decisions)
