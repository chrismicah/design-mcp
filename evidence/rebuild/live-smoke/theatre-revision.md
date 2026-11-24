# Theatre call sheet revision

**Visual verdict: rejected.** The owner rejected both the original dark dashboard and the revised call sheet shown at 390 px. The filter and restore results below are functional evidence. Keep both screenshots as examples of the visual quality gap.

The original dispatch direction specified a dark exception strip, queue and status rail. The agent repeated the same two rooms in the summary, list and support rail. On mobile it changed the visual order without changing the document order.

## Product fix

`direct` now selects `stage-call-sheet` for theatre turnaround and stage-management briefs. The direction makes the room list the composition, using cream paper, large Newsreader room names, and a burgundy cell for the actual delay. The prompt-book reference informed the placement of a cue beside its corresponding line. The color, typography and filter are adaptations. The general handoff calls for dropping redundant supporting regions and aligning visual with document order. [Theatrecrafts reference](https://www.theatrecrafts.com/pages/home/topics/stage-management/the-prompt-book/)

The same vague “make this feel premium” wording now yields different directions for theatre and freight in the actual v2 stdio server. No explicit surface was supplied and both calls returned zero questions. All 308 tests passed. [Tool outputs](theatre-revision-stdio.json)

## Browser proof

The current GPT session used the new tool output to author the [reference HTML](theatre-revision.html). This is a reference implementation of the new direction. A fresh independent generation in a separate client is still open.

| Layout and input | Observed result |
| --- | --- |
| Desktop click on Delayed only | Hall A left the list. The filter was pressed and the status named the six-minute delay in Studio B. |
| Desktop click on All rooms | The two original rooms returned and the live status said both rooms were shown. |
| 390 px keyboard | Tab and Enter changed the filter. Shift+Tab and Enter restored both rows. Focus remained on the activated control. |
| 390 px geometry and type | The document and content widths both reported 390 px. Newsreader and Instrument Sans loaded. |

Asset hashes are below. Screenshots are kept local in `.context/rebuild/theatre-revision/`. The static checker returned zero findings. The previous board also scored zero, so the count does not resolve the owner's visual objection. Reduced motion is respected in source, with browser emulation outside this check.

| Asset | SHA-256 |
| --- | --- |
| `theatre-revision.html` | `52bc4c6d0b30074162361752e694135ebe7182eedb9186c58c059cb89bdcc9a7` |
| `desktop.png` | `4efb645b54d3e6d48fb29745a3f0c79c79cac441a189fc6e72e65312d32e748c` |
| `turnaround-390.png` | `b0ac8842b102140a40c54fe17ec2dfeec28f5d42c45ac54d7bc18f2474a00632` |
