# Changelog

## Unreleased

- Added the 36-brief matched benchmark with clean-session token accounting, Playwriter captures, blind judging, and competitor adapters. The first seven judged briefs averaged 92.9 without the MCP and 95.2 with it. [Benchmark](EVALS.md)
- Added `design-mcp doctor`, offline directions, and lazy loading of the checksum-verified legacy corpus. Fresh pipx and uv installs exercised all 17 tools with Python 3.10–3.13 on both Intel and Apple Silicon macOS 15. The client examples use the installed command. [Install results](EVALS.md#candidate-decisions)
- Tested four credential-free design tools over stdio. Their full visual comparisons are pending. [Competitor preflight](teardown/COMPETITORS.md#installed-tool-preflight)
- Measured compact computer-vision context against full-size screenshots and specified a fast local first review before frontier vision. [Vision research](research/VISION.md)
- Made the planner, builder, and independent evaluator workflow standard. Added recurring public source discovery and connected the visual release verdict to the exact browser captures. [Development harness](DESIGN-HARNESS.md)

The form-routing branch remains a candidate. Visual acceptance is tracked in the benchmark. [Candidate decisions](EVALS.md#candidate-decisions)
