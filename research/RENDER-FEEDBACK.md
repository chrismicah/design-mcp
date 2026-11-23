# Use measured browser feedback before visual judging

## Test this first

Freeze the visitor's intended task, the visible factual details, and the controls required at each viewport. Preserve them across repair passes. Measure the browser's actual boxes and task outcomes, then supply only the failing checks before a scoped revision. Keep the full original captures and the exact source hash for later review. Judge the final live design separately for originality, craft and usability.

LiveWorkspace uses a shared representation of the target and current render, then passes their structured differences to a coding model. In its matched-budget screenshot reconstruction comparison it reports improvements of 1.8 points on Design2Code and 2.0 on ScreenBench. On a separate five-round subset, retaining the target reduced reported input and output token usage by 42.7% and 15.7%. The authors identify unreliable element matching and gaps in responsive and interactive coverage. The practical test for this repository is to keep the same checked target and pass actual browser measurements alongside it once per revision. Preserve the measured task outcome and record elapsed time and token use per arm. The paper's results concern reconstruction and provide no visual score for original designs. [LiveWorkspace, Sections 4.2, Limitations, and Appendix D](https://arxiv.org/html/2611.12112v1)

## Verify the revision separately

1D-Bench records whether a page renders before it credits similarity, and provides runtime failures to the builder on later rounds. For this project, record rendering and action failures separately and exercise the keyboard route again after a repair. Keep failures in the denominator and include the clean generated draft, the matched repair control, and the arm receiving the measured MCP reply. Expect fewer unresolved geometry failures if structured feedback helps. Measure that expectation rather than extrapolating perfect behavior from a single viewport or model. [1D-Bench, Sections 3.2–4.2](https://arxiv.org/html/2602.18548v1)

Anthropic's evaluator interacts with running applications and checks the negotiated acceptance contract. Use deterministic measurements for geometry, actual input for functionality, and a fresh skeptical critic for taste. Have the critic identify what would be harder to do in one version and what makes its visual treatment specific to the subject. Budget one measured revision before spending a vision pass on a candidate with known failing interactions. [Anthropic's harness report](https://www.anthropic.com/research/harness-design-long-running-apps)

320 CSS pixels is a reflow test width for horizontally written content. W3C describes vertical scrolling as an ordinary way to read reflowed content. The 700 px opening height and visible preview button are specific to the short-call preparation benchmark. Record reflow and initial task placement independently. Require task-specific evidence before recommending that any controls move above the fold. [W3C Understanding Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow)


## Measured overhead

With a warm stdio connection on the shared arm64 Mac, the trial's 30 measured replies had **2.91 ms p95** and 893 bytes of structured JSON. The same process returned the ordinary reaction at **2.68 ms p95** and 394 bytes over 30 calls. Browser work, startup and model use are outside these measurements. This records the cost of requesting the feedback. The matched repair test will establish its effect on the rendered result. [Timing samples](../evidence/benchmark-v1/opening-view-reaction-overhead.json)

## Clean install replay

Both pipx and uv reproduced the exact measured reply and all six unchanged reaction cases on macOS 15 with Python 3.13, on Intel and Apple Silicon. Intel passed after one rerun. The first attempt passed the default stdio checks and timed out during a combined-surface tool call. The first log leaves the tool name unknown. [Install receipts](../evidence/benchmark-v1/opening-view-reaction-installed.json) · [Hosted run](https://github.com/chrismicah/design-mcp/actions/runs/45280229322/attempts/2)

## Matched repair outcome

Both low-effort Terra sessions received the same frozen Tacoma page and the same repair brief. The only prompt change was the installed measured reply in the treatment. The browser replay verified unedited HTML and all original frame hashes.

At 320 × 700 the frozen preview ended at 867.66 px. The control placed the call-preparation area before the separate service list and ended at 627.39 px. The measured arm kept the separate list above the form and ended at 740.47 px. The name field fit in both. At 390 and 1440 px both revisions passed. All six keyboard journeys recovered from a blank name, kept the service choice, produced an editable reminder, and sent zero post-load requests. Generation took 59.09 seconds and 3,060 output tokens for the control, and 57.22 seconds and 2,976 output tokens for the measured arm. The treatment added 227 input tokens in this pair.

Decision: keep the measured reaction on its trial branch. It improved the frozen page and missed the opening action that the matched control reached. The score gate stays open. A stronger follow-up should test whether giving the model a task-specific replacement for the repeated service list helps over the same ordinary repair, and should use a different holdout before any promotion. [Matched browser results](../evidence/benchmark-v1/opening-view-reaction-comparison.json) · [Original Chrome artifact](https://github.com/chrismicah/design-mcp/actions/runs/45282461449)
