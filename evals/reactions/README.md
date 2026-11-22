# Design acceptance with short reactions

This suite uses six existing project briefs and four short user prompts per brief. It tests how quickly a non-designer can use plain language to get a usable, distinctive first draft, then ask for a narrow change. The 24 prompt cases belong to a separate benchmark series. [Target user and acceptance rationale](../../research/RESEARCH-USER.md#acceptance-experiment)

## Run the same conversation in each arm

1. Verify the source brief file against the hash in `tasks.json`. Remove the source brief's leading style request by splitting once at the first period followed by a space. Give each generator the remaining text as project context and one exact user prompt from the case. Use the same model, client, asset policy, and time budget in both arms.
2. Log any question verbatim and take its recommended answer when one is available. Record each answered question, tool call, rendering time, and model usage separately. Answer at most two questions and record any excess as a failure.
3. A separate blind reviewer opens the build, attempts the stated action at 1440 and 390 CSS px, and checks focus, reflow, and the visible result. Save original captures, a squint view, the static tell check, and comparisons with two or three relevant award examples. Use the standing weighted rubric on every required screen. [Live rubric](../vision/rubric.md)
4. If the first build misses, send the next exact reaction from `tasks.json`. In the candidate arm the client may call `react`. The control receives the same words and timing rule. Reopen the revised build, verify the primary action and protected facts, and record the changes the user can actually see. Stop on the first pass or after the two supplied reactions.
5. Report clear first-pass rate, time to first pass, steps per case, percentage passing within two reactions, and paired blind preference. Include misses and timeouts in the denominator. This is a simulated-user experiment.

For a revised version of this suite, record changed prompts, response rules, preserved facts, and the reason before launching a comparison. Keep the original prompts and results readable.
