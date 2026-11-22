# Website review release critic

Use a fresh evaluator session. Supply the task, randomized screenshots with original pixels at desktop and 390 CSS px, and independently observed browser facts. Keep the author, branch, candidate identity, and prior ratings hidden. Score each required screen separately from 0 to 10.

| Criterion | Weight | Review question |
| --- | ---: | --- |
| Design coherence | 30% | Do type, spacing, color, imagery, and controls feel like one intentional composition that fits this task? |
| Originality | 30% | Can you name a creative choice that only makes sense for this subject? Unadapted component defaults and generic decoration count against the score. |
| Craft | 20% | Are alignment, hierarchy, contrast, proportions, and the typographic rhythm precise at this width? |
| Usability | 20% | Can someone locate and understand the next action immediately? Do the visible states and reading order support the work? |

Score 5 for a basic result with material weaknesses, 7 for a usable and coherent design with limited distinction, and 9 for strong work with a visible opportunity for improvement. Use 9.5 or above only for a cohesive, distinctive result with no material visible weakness. Name every weakness with the affected region, the observed problem, a proposed repair, and the expected change. Give strengths the same specificity.

Calibrate with separately labeled samples before reviewing anonymous candidates. The owner rejected the earlier theatre dashboards even though their filters worked. Use those to calibrate the difference between a working control and a convincing visual composition. Keep the unknown candidates blind. [Calibration receipt](../../evidence/rebuild/live-smoke/theatre-revision.md) · [Harness research](https://www.anthropic.com/engineering/harness-design-long-running-apps)

The release decision requires at least 9.5 for every required screen and an independent pass for the primary action, responsive geometry, privacy, and speed. A material finding blocks acceptance. Use the smallest observable repair and render the next candidate with unchanged conditions. Keep the strongest checked iteration and pivot when the same approach stalls.

## Verify a verdict

The browser receipt records the independent checks in `checks`, the hash of its observations in `evidence_sha256`, and a `captures` map from required screen ID to original image SHA-256. Set the IDs from the acceptance contract before review. When unblinding, join each ballot screen's anonymous label to its actual image and attach `capture_sha256`. The model only needs the anonymous labels and the images.

```sh
python3 evals/vision/score.py --ballot ballot.json --browser browser.json \
  --browser-evidence observations.json \
  --screen desktop --capture desktop desktop.png \
  --screen mobile --capture mobile mobile.png
```

Exit 0 means the submitted ballot and browser checks passed for those capture files. Exit 2 means a criterion failed or the records and files disagree.
