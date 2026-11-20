# Source challenge response

Fable reviewed landing, dashboard, and mobile without launching a browser. Preserve the original experimental output hashes. The files in `challenged/` are the separate fix pass.

| Finding | Resolution in the fix pass |
| --- | --- |
| Named faces declared without loading | The tool returns a stylesheet URL built from the licensed family selections. Each fix-pass page declares the stylesheet. Confirm active faces at render. |
| Cart updates and bottom action | The added status role makes the result explicit. Mobile sticky action padding respects the safe-area inset. |
| Dashboard toggle, row selection, and focus | Keep the toggle label stable with `aria-pressed`. Filter by load ID and leave focus on the toggle. Put the table in a labelled keyboard-scrollable region. |
| Ticket disclosure announcement | Keep the native button and its expanded state. Remove the additional live region. |

The source checker remains frozen for the comparison. Its original zero counts remain source-only results. The fix pass still needs action, type load, and 390 px receipt under the shared render lease. [Independent source review](challenge-review.md)
