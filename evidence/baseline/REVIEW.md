# Review: baseline experiment (A) and static-check draft (B)

Reviewer: coordinator `eb3116f5` (Claude Fable 5.2), not the author of either. Read-only; no product, prompt or branch changes.
Read: `evidence/baseline/briefs.json` (ids, surfaces, first 70 characters of each brief), `.context/rebuild/experiment.md` (in full), the rule header and rule ids of `draft/design_checks.py`, the three test names. **Not read:** the body of `inspect_design`, the test bodies, the legacy receipts, the rest of each brief.
Independent probe: 12 inputs I wrote, run through `inspect_design`. Inputs and findings: `.context/rebuild/review-ab-probes.json`.

## Verdict

- **A: usable with three changes before generation continues** (A1–A3).
- **B: not ready to be the outcome measure.** It misses the brand-font tell in every common way of declaring a font, and the misses are likely to differ by arm (B1).

## B. Static checker: probe results

| Probe | Fired | Finding |
|---|---|---|
| Banned-tell JSX sample (9 tells) | 7 rules | Missed `brand-font` (`fontFamily:` in JSX), the emoji, the three-card grid |
| `--f:'Inter'` + `font-family:var(--f)` | none | **B1** miss |
| `font:16px/1.5 Inter,sans-serif` | none | **B1** miss |
| Google Fonts `family=Inter` link only | none | **B1** miss |
| `'Inter Tight'`, `'Roboto Slab'` | `brand-font` | **B2** prefix match treats different faces as banned |
| `'Fraunces',Inter,system-ui,serif` | none | Correct: fallbacks ignored |
| `linear-gradient(135deg,#667eea,#764ba2)` | none | **B3** purple gradient missed; rule matches a hex list, not hue |
| "Now elevate your roast", "Unlock seamless brewing" | none for these | **B4** copy rule is anchored to the start of the text |
| "Start your free trial!", "Get Started Free", "✅ Fast" | 3 rules | Correct |
| Three identical rounded shadow cards, plain HTML | `rounded-shadow` only | **B5** `symmetric-cards` exists but did not fire |
| `*{text-align:center}` on every section | none | **B5** centring only seen as a utility class |
| Clean page with "Indigo-dyed", "Blue Ridge" in copy | none | Correct: no false positive on colour words |

Actions:
- **B1 (blocking).** Resolve the first family through custom properties, the `font` shorthand, JSX `fontFamily`, and `@font-face`/font links. Generated pages usually declare fonts through variables, so today a zero count means "not seen", not "absent". If one arm's outputs use variables more than another's, the static count is biased toward it.
- **B2.** Match whole family names and decide `Inter Tight`, `Roboto Slab/Mono/Flex` explicitly.
- **B3.** Classify gradient stops by hue from any hex, rgb or hsl value.
- **B4.** Match banned copy anywhere in headings, buttons and links.
- **B5.** Fire `symmetric-cards` on repeated sibling structure and centring on universal or body selectors, or mark both as rendered-only.
- **B6.** Emit a "not checked" list with every result. No rule id exists for single font or weight, bold-body headings, identical section padding, alternating grey bands, imagery, overlays, absent motion, or reduced-motion. Without the list, zero findings reads as a pass.
- **B7.** Add the 12 probes as fixtures. All three existing tests were written by the checker's author.

## A. Experiment design

- **A1. No clear-prompt stratum.** All six briefs open with a vague adjective ("Make it premium", "Make it pop", "Idk make it good"). The plan's target of a passing first render on clear prompts cannot be measured, and no brief carries a misleading instruction such as "throw some glass cards at it". Add at least two clear and one misleading variant, or drop those targets.
- **A2. Arm L depends on an experimenter choice.** L gets a pre-captured legacy receipt. Record the tool, arguments and character count per receipt. A legacy search response measured 86k–169k characters; arm D's envelope is capped at 6,000. Context size is confounded with arm unless reported.
- **A3. Freeze the measure first.** Hash `design_checks.py` and the scoring rubric before any arm D output exists. Rules tuned after seeing outputs cannot support a comparison.

## Limits of a shared author across arms

`experiment.md` asks for independent sessions "if possible". Where one model session produces more than one arm:

1. **Carry-over.** The later arm has seen the earlier design; contamination runs both ways and order is not randomised.
2. **Arm awareness.** The generator can know which arm is the baseline. Only the quoted instruction, the brief and the arm's receipt should be in its context; the sentence describing the arms should not.
3. **Prior exposure.** A session that has read the banned list or the plan is not a naive baseline. That inflates arm N and understates any gain; it must be recorded per session.
4. **One sample per cell.** Six briefs × one output per arm gives no variance estimate, so a difference cannot be separated from run-to-run noise. Two repeats on two briefs would give a floor.
5. **One model.** Results describe that model only.
6. **Scoring.** The scorer must not be the generator and must not see arm labels; hash outputs before scoring.

Minimum affordable control: one fresh session per arm, brief order randomised, session ids and context contents logged, and items 2, 3 and 6 enforced. Without that, report results as a pilot observation, not a comparison.
