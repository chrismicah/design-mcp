# Slice E comparison receipts

The source comparison uses the checker frozen in A. N and L are the original, independent GPT-6.2 Astra baseline sessions. D consumed only the `direct` response and the original rendering prompt on a second turn in N’s session. C consumed the same response stripped of its rationale, sources, and credit on a second turn in L’s session. Conductor refused fresh sessions under host memory pressure. Session carry-over can affect the pilot and limits causal conclusions.

Six D pages and three C pages were generated. The legacy and no-MCP baselines each receive six source checks. The source receipt retains every finding and hash. [Frozen source checks](source-results.json)

Playwriter reopened the three matched briefs for all four arms at 1440 and 390 CSS px. All 24 checks reached the primary control by Tab and observed its expected state change after Enter. The coffee pages added one bag, the load boards focused LS-057, and the train pages revealed TKT-0837. All 24 captures had no horizontal overflow or page errors. The browser receipt links the original, blurred and after-action image hashes to the preserved HTML. [Browser receipt](hosted-pilot-browser.json) · [Capture run](https://github.com/chrismicah/design-mcp/actions/runs/44990418447)

| Brief | Plain | Legacy | Ablated direction | Full direction |
| --- | ---: | ---: | ---: | ---: |
| Coffee launch | 9 | 9 | 9 | 7 |
| Dispatcher board | 9 | 5 | 10 | 10 |
| Train ticket | 8 | 9 | 10 | 8 |

The full coffee direction's pack illustration pushed the roast date below the mobile viewport and left the purchase button detached from the desktop facts. Both dispatcher directions made the delay and its action easy to find at both widths. The full train direction separated the time from the platform and hid the 08:58 alternative behind a generic label. All frozen views returned an empty loaded web-font list. [Coffee ballot](pilot-landing-ballot.json) · [Dispatcher ballot](pilot-dashboard-ballot.json) · [Train ballot](pilot-mobile-ballot.json) · [Pilot rubric](../benchmark-rubric.md)

## Slice G decision

**Repair and rerun the affected briefs before broad rollout.** The full direction averaged 8.33/10 across the three briefs, compared with 8.67 for the plain generator, 7.67 for legacy, and 9.67 for the ablated direction. It lost the coffee brief to both controls and the train brief to legacy. Equal keyboard outcomes and fewer source tells leave those visual losses unresolved. Keep the dispatcher direction, which scored 10 and passed its actions.

The ablated arm used a different preceding session from the full arm. The result justifies a clean replay before changing how much rationale the tool returns. The repair branch `a18e08d` makes the product art shallower, puts the buy control next to the required facts, groups the three departure facts, and carries the later departure time onto the closed row when supplied. Source tests and route checks passed. Fresh matched renders will test whether those changes carry through. Contrast verification and the broad rollout gate remain open. [Rollout plan](../../../PLAN.md)

### Fresh repair comparison against plain generation

The coffee repair tied the plain generator at **95.8**. The train repair scored **95.8** against **87.5** for plain generation. The independent critic rated the train repair higher on accessibility. Its browser tree exposed named actions for Show ticket and Later departure 08:58, a labeled Weekly pass checkbox, and a ticket status region. The first capture showed the ticket closed. A separate keyboard check covers whether opening the ticket shows TKT-0837. Each pair used the same prompt, model, effort, browser, asset policy, and original six-criterion rubric. The comparisons against fresh v2 and legacy remain separate. [Blind ballots and token receipts](../../benchmark-v1/pilot-repair-vs-plain.json) · [Matched Playwriter captures](https://github.com/chrismicah/design-mcp/actions/runs/44995046174)

### Fresh repair comparison against v2 and live interaction

Coffee scored **100.0** with the repair and **91.7** with fresh v2. Train scored **95.8** and **87.5**, respectively. These are separate blind comparisons of initial captures under the original six-criterion rubric. The train critic cited the smaller gap between departure details and the ticket control, and the named controls and status region in the browser tree. [Blind ballots and receipts](../../benchmark-v1/pilot-repair-vs-v2.json)

Playwriter passed all **12** action checks across the three arms and two widths. For coffee, the repair confirmed the addition inline. Tab reached Bag, which held one Alto Carmo at $19. Escape closed it and restored focus. On mobile, the repaired buy action starts at y=614 CSS px versus y=780 for fresh v2. For train, both widths exposed 08:58 before opening the ticket. Enter revealed TKT-0837 and a second Enter closed it with focus on the same control. [Matched action receipts](../../benchmark-v1/pilot-repair-actions.json) · [Live Playwriter run](https://github.com/chrismicah/design-mcp/actions/runs/44995952011)

The rebuild branch includes both directions. The train revision entered at `a7d1019`. All 36 routes matched the previous branch. Only the train brief changed its response, and all responses fit within 6,000 characters. The integrated suite passed 358 tests and exercised all 17 stdio tools. The fresh comparison with the historical MCP is running.
