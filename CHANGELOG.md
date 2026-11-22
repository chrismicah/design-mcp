# Changelog

## Unreleased

- Added the 36-brief matched benchmark with clean-session token accounting, Playwriter captures, blind judging, and competitor adapters. The first two release-baseline briefs averaged 91.7 without the MCP and 95.8 with it. [Benchmark](EVALS.md)
- Verified the installed package on Intel and Apple Silicon macOS 15 with Python 3.12 and 3.13 using pipx and uv. Replaced the old machine-specific Claude Desktop example with the installed command and documented Claude Code user scope. [Install results](EVALS.md#installation-at-the-baseline-revision)
- Tested four credential-free design tools over stdio. Their full visual comparisons are pending. [Competitor preflight](teardown/COMPETITORS.md#installed-tool-preflight)
- Measured compact computer-vision context against full-size screenshots and specified a fast local first review before frontier vision. [Vision research](research/VISION.md)

The form-routing and portable-package branches remain candidates. Visual and install gates are tracked in the benchmark before integration. [Candidate decisions](EVALS.md#candidate-decisions)
