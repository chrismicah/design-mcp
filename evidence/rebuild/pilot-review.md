# Review C, final: `design_mcp/data/directions.json`

Reviewer: coordinator `eb3116f5`. One scripted pass over the six records plus a grep of the API draft. No full reread, no render.

## Verdict: 6 of 6 accepted for the pilot. None accepted yet as proof of generalisation.

| Earlier blocker | Now |
|---|---|
| Fictional brief facts in records | **Cleared.** No brand, product, ticket or price string from the six briefs remains; ids are generic |
| All light, warm paper | **Partly cleared.** `exception-first` is dark (paper luminance 0.01). Five are still light. The cool-paper claim was not checked (luminance only) |
| Motion | **Cleared.** All 240–400 ms with a reduced equivalent; `margin-front` now triggers on tap or keyboard; `ground-plane` is 400 ms |
| Similar-serif pairing | **Cleared.** `margin-front` body is Source Sans 3 |
| Licences | 11 entries; all 12 face names appear in `font-licenses.json`. I checked presence, not the receipts |
| Button text, focus, easing | Supplied by the API draft (`accent_foreground`, `ease-out`, focus rule) |
| `exception-first` source | Now one source at `evidence`. I did not reread the receipt, so I cannot confirm it supports the claim |

## Remaining limitations

1. **Train-on-test.** The records were authored from the six test briefs. Genericising the wording does not change that; held-out briefs are still required before any comparison claim.
2. **Focus ring may be invisible.** The API specifies a `currentColor` ring with 3 px offset. On a filled button whose text is the paper colour, that ring is paper on paper. Verify in a render or use ink.
3. **No variation.** `direct` takes no seed and there is one record per surface, so the same brief type always returns the same direction. Selection uses token matching against the brief.
4. **Two accents remain close** (`exception-first` hue 24, `margin-front` hue 15), and Atkinson Hyperlegible is still the body face in two of six.
5. **`platform-sign` accent on paper is 1.4:1.** Safe only as a fill under ink; I did not confirm the record says so.
6. **Single-source records:** `exception-first`, `scale-ledger`, `margin-front`.
7. **No slot markers.** Records are generic prose; nothing forces the agent to fill in the brief's own facts.
8. **Nothing rendered.** Photo-overlap and legibility fixes are unverified by me.
