# Slice A baseline

Six fixed fictional briefs exercise marketing, operational, mobile web, portfolio, pricing and editorial use cases. The no-MCP and legacy-MCP generators use the same Astra model and instructions, with independent sessions. The legacy context consists of a filtered search result and the legacy design system response, with original call arguments stored in the receipts.

The common implementation request is:

> Build a polished, working single-page HTML implementation of the supplied request. Use HTML, CSS and vanilla JS in a self-contained file. Keep the main action usable with keyboard and at 390 px. Use available design tool guidance if supplied. Deliver the HTML only.

Treat the comparison as a small experiment. Independent sessions isolate the two arms, while the generators see multiple briefs within each arm. Legacy responses vary in size and give the model an additional design constraint. The first set measures everyday requests with vague adjectives. Clear, misleading and minimal-input variants and held-out content belong to expansion QA.

| Arm | Generator | Context |
| --- | --- | --- |
| N | GPT-6.2 Astra, `912666b0` | Frozen requests only |
| L | GPT-6.2 Astra, `179daf1b` | Frozen requests and a legacy tool envelope from `82fe6e3` |

The capture script records source and image hashes, 1440 and 390 viewport metrics and blurred grayscale images in the local QA directory. These are headless captures.
