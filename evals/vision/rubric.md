# Live design release rubric

Use a fresh evaluator session separate from the builder. Give it the task and the anonymized live build. Keep the author, branch, candidate identity, and prior ratings hidden. The evaluator opens the build, confirms the expected screen, navigates and chooses an input for the primary action and a relevant edge state before scoring. Use Playwriter for websites, XCUITest or macOS Accessibility for Swift, and Playwright on the packaged Electron app with native accessibility for menus. Record observed outcomes and before-and-after captures. Preserve the evaluator's interaction trace. On the web, check desktop and 390 CSS px. Score every required screen separately from 0 to 10. A witnessed task failure lowers functionality. Missing live evidence leaves the round unscored. [Standing design principles](../../DESIGN-STANDARD.md)

| Criterion | Weight | Review question |
| --- | ---: | --- |
| Design quality (`coherence`) | 30% | Do type, spacing, color, imagery, and controls feel like one intentional composition with a mood and identity that fit this task? |
| Originality | 30% | Can you name a creative choice that only makes sense for this subject? Unadapted component defaults and generic decoration count against the score. |
| Craft | 20% | Are alignment, hierarchy, contrast, proportions, and the typographic rhythm precise at this width? |
| Functionality (`usability`) | 20% | Can someone locate the primary action, complete the task, and tell from the result that it worked? |

Score 5 for a basic result with material weaknesses, 7 for a usable and coherent design with limited distinction, and 9 for strong work with a visible opportunity for improvement. Use 9.5 or above only for a cohesive, distinctive result with no material visible weakness. Name every weakness with the affected region, the observed problem, a proposed repair, and the expected change. Give strengths the same specificity.

## Calibration

Calibrate on three independently scored development examples before reviewing candidates with this rubric version. Include a polished design with a broken primary action. Withhold the third example's rating until the evaluator grades it and compare criterion-level reasoning. Keep the calibration examples and close variants out of the 36-brief benchmark. These hypothetical anchors illustrate the scale. Within each row, the four ratings follow the order above.

| Anchor | Observation | Ratings | Weighted score |
| --- | --- | --- | ---: |
| Routine result | The room filter works. Repeated cards give the late room and ready rooms equal weight, and the look could belong to any dashboard. | 5, 3, 6, 7 | 5.0 |
| Coherent result with friction | A repair intake reads in task order and uses clear labels. Its layout is familiar, and an invalid phone number leaves the keyboard user at the wrong field. | 8, 6, 8, 7 | 7.2 |
| Exceptional result | A listening schedule communicates airtime through a distinct tuning-strip composition. Listeners find the next program, open its details, and return to their place with visible focus at both widths. | 9.5, 9.5, 9.5, 10 | 9.6 |

The owner rejected the earlier theatre dashboards even though the filter worked. Use the preserved design and interaction evidence to clarify why functionality alone does not carry design quality or originality. Keep those examples out of the blind comparison. [Theatre receipt](../../evidence/rebuild/live-smoke/theatre-revision.md) · [Harness research](https://www.anthropic.com/engineering/harness-design-long-running-apps)

The release decision requires at least 9.5 for every required screen and an independent pass for the primary action, responsive geometry, privacy, and speed. A material finding blocks acceptance. Use the smallest observable repair and render the next candidate with unchanged conditions. Keep the strongest checked iteration and pivot when the same approach stalls.

## Verify a verdict

Set screen IDs and tasks before review. Save the evaluator's observations as JSON. Include the observed `build_sha256`, `builder_session`, and `evaluator_session`. Under `screens`, each required ID has an `opened` string identifying the live screen, `before_sha256` and `after_sha256` for its captures, and an `actions` list. Each action records `input`, `expected`, and `observed`. Retain the test runner trace showing build identity, actor, actions, and results.

The browser receipt records the independent checks in `checks`, the `build_sha256`, the hash of the observations file in `evidence_sha256`, and `before_captures` and `captures` maps from screen IDs to original image SHA-256. After unblinding, add the matching `build_sha256`, `evaluator_session`, and `live_review_sha256` to the ballot and each after-capture hash to its screen as `capture_sha256`. The verifier checks the packet and original file bindings. Confirm from the trace that the evaluator operated the target and observed the outcomes.

```sh
python3 evals/vision/score.py --ballot ballot.json --browser browser.json \
  --browser-evidence observations.json \
  --screen desktop --before-capture desktop desktop-before.png --capture desktop desktop.png \
  --screen mobile --before-capture mobile mobile-before.png --capture mobile mobile.png
```

Exit 0 means the submitted ballot and browser checks passed for those capture files. Exit 2 means a criterion failed or the records and files disagree.

## Verify a creative series

Use `python3 evals/vision/score_series.py series.json` before promoting an expressive web design. It verifies the underlying files for 5–15 distinct revision builds, and the fresh evaluator's confirmation of the exact finalist. Keep below-threshold rounds in the series. Record the main criticism in each round and the visible response in the following round. A concept-only discussion belongs in the research log.

Keep the evidence files inside the manifest's directory. The `build` file contains the exact served standalone HTML, or a frozen bundle when the browser receipt identifies it as the build. Use both `desktop` and `mobile` captures. For example, a round entry has this shape.

```json
{
  "premise": "Open the cut inside the sentence",
  "critique": "The source clock reads like the player position",
  "revision": "Place the edition name beside its clock",
  "review": {
    "build": "round-2/index.html",
    "ballot": "round-2/ballot.json",
    "ballot_sha256": "<SHA-256 of ballot.json>",
    "browser": "round-2/browser.json",
    "browser_sha256": "<SHA-256 of browser.json>",
    "observations": "round-2/observations.json",
    "before": {"desktop": "round-2/desktop-before.png", "mobile": "round-2/mobile-before.png"},
    "after": {"desktop": "round-2/desktop-after.png", "mobile": "round-2/mobile-after.png"}
  }
}
```

Put entries in the `rounds` array. Set `finalist_round` to its one-based position. Set `confirmation` to the second evaluator's review object, with their own receipt and captures. The first round may omit `revision`. Verify that the trace supports the blinded review and shows the archived build serving those captures. Confirm that changes respond to the critiques and the finalist wins its matched comparison. The verifier checks file identity, recorded sessions and score requirements.
