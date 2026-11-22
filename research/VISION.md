# Website review with browser evidence and frontier vision

## Calibration

The renderer captured the same two matched briefs with Chrome for Testing and Playwriter MCP. The full-input judge saw four original screenshots with an accessibility excerpt. The compact judge saw the original 390 px screens, two 720 px desktop images, and the visible regions' CSS boxes, labels, active type, ink, fills and pressed states. The same frontier model and scored rubric ran in separate blind sessions. [Capture run](https://github.com/chrismicah/design-mcp/actions/runs/44985648610) · [Both ballots and token receipts](../evidence/benchmark-v1/compact-vision.json)

| Judge input | Tokens in | Tokens out | Rehearsal rooms | Ceramics |
| --- | ---: | ---: | --- | --- |
| Full | 51,112 | 7,755 | MCP win | Tie |
| Compact | 48,695 | 7,256 | MCP win | Plain generator win |

Compact input used 4.7% fewer input tokens. One of two preferences changed. The two independent readings cannot isolate image resolution, extra geometry, or model variation. Keep full-resolution evidence for the release critic. Use compact browser observations to locate and describe issues before sending images to a frontier model.

At 390 px, the collected theatre evidence located “Delayed only” at `[138, 239, 118, 44]` in CSS pixels, identified its active type and unpressed state, and located the two-room status. A separate browser action changed the visible list, pressed state and status and then restored them. Geometry can establish what fit and what moved. A design judgment can assess whether the exception and next action are legible at a glance. [Browser interaction receipt](../evidence/benchmark-v1/preflight.json)
