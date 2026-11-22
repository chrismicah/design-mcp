# Changelog

## Unreleased

- Added the 36-brief matched benchmark with clean-session token accounting, Playwriter captures, blind judging, and competitor adapters. The first eight judged briefs averaged 93.2 without the MCP and 95.8 with it. [Benchmark](EVALS.md)
- Added `design-mcp doctor`, offline directions, and lazy loading of the checksum-verified legacy corpus. Fresh pipx and uv installs exercised all 17 tools with Python 3.10–3.13 on both Intel and Apple Silicon macOS 15. The client examples use the installed command. [Install results](EVALS.md#candidate-decisions)
- Tested four credential-free design tools over stdio. In the first matched browser comparison, hosted Inspo scored 87.5 on ceramics and Design MCP scored 91.7. [Competitor results](teardown/COMPETITORS.md#visual-scoreboard)
- Measured compact computer-vision context against full-size screenshots and specified a fast local first review before frontier vision. [Vision research](research/VISION.md)
- Made the planner, builder, and independent evaluator workflow standard. Added recurring public source discovery and connected the visual release verdict to the exact browser captures. [Development harness](DESIGN-HARNESS.md)

The form-routing branch remains a candidate. Visual acceptance is tracked in the benchmark. [Candidate decisions](EVALS.md#candidate-decisions)
