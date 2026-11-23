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
