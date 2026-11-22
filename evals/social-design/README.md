# Social design comparison

Compare the current Design MCP catalog against two directions derived from sites discussed on X and Reddit. Keep the direction candidates in this directory until they pass a matched browser comparison. Use the same two creative briefs and one permit form in both arms. The existing 36-case task file and runtime catalog are the controls.

## Acceptance contract

| Task | What should make it distinctive | Live check at 1440 and 390 px |
| --- | --- | --- |
| Stage lighting portfolio | The image of a lit stage is the work sample and responds to the selected cue | Open Flood without a pointer, read blue backlight, switch to Static and confirm the light scene and written cue change with focus visible |
| Rising river editorial | Actual elevations organize one continuous river section. Each selectable level changes what the reader can see and learn | Jump directly to 6 m, then to 2 m. Confirm the correct closures in the scene and in readable text. Repeat with reduced motion |
| Permit form | The next answer and the available outcome should lead the page | Try an empty submission, correct it and confirm the result. Keep all fields and the primary action reachable by keyboard |

Give the critic the original tasks and anonymous builds only. Use the [live rubric](../vision/rubric.md) and grade the primary states from both widths. Ask which subject-specific idea survives a five-second glance, and require before-and-after captures for every functionality verdict. The candidate must improve originality on both creative briefs without a drop in functionality, preserve the form route, and meet the standing 9.5 release threshold before promotion.

## Art direction for the creative candidates

**Lighting folio.** A producer deciding whether to book a theatre lighting designer should feel the instant before a show starts. The selected cue drives a full-width stage cross-section. A row of named cues leads to a technical note. Remove the carousel, generic services grid and staged photography. Use dark aubergine `#241826` for ink, light lavender `#F1E6F0` for reading paper, and violet `#69385C` for the selected cue. Amber `#E8AD54` and ice blue `#91C2E8` belong to examples where the brief supplies those cues. Bricolage Grotesque gives the production titles weight, and IBM Plex Sans sets the cue notes. The focal detail is the boundary where the light cuts across the stage.

**River levels.** A resident trying to remember which crossing is open should feel the physical change in the water level. Put the bank and visible height rail next to the affected places. Keep three named level controls and put the selected effect in text close to them. Remove scenic flood photography, a generic statistics grid and autoplay. Use navy `#152C39` for text, pale blue-gray `#EAF0EF` for reading paper, and deep teal `#216373` for the active level. Slate `#70848A` marks the bank, and gold `#E4B659` locates closed infrastructure alongside a text label. Barlow Condensed marks elevations, and Source Sans 3 sets explanations. The focal detail is the water line passing a place people use.

## Run the comparison

Run from the repository in an environment where `python3` and `design-mcp` point to the same checked-out revision and installed dependencies. Use one generation per brief per arm before deciding whether to spend quota on another round. The same task file and verbatim prompt go to both arms.
Use the same low-cost coding model and effort in both generation arms. Run the critique in a separate session with an efficient vision model. Reserve a frontier model for planning and arbitration.

```sh
python3 evals/v1/generate.py --tasks evals/social-design/tasks.json \
  --server "$(command -v design-mcp)" --treatment-only --out "$CELLS" \
  --model "$MODEL" --effort low --no-shell --quota-probe "$QUOTA_PROBE" \
  --require-unhinted-direct --expect-direction social-lighting=ground-plane \
  --expect-direction social-river=margin-front \
  --expect-direction social-permit=grouped-fieldsets

python3 evals/v1/generate.py --tasks evals/social-design/tasks.json \
  --server evals/social-design/serve.py --treatment-only --treatment-label social \
  --out "$CELLS" --model "$MODEL" --effort low --no-shell --quota-probe "$QUOTA_PROBE" \
  --require-unhinted-direct --expect-direction social-lighting=cue-stage \
  --expect-direction social-river=level-cross-section \
  --expect-direction social-permit=grouped-fieldsets
```

Generate the critic tasks and run the existing live review. Repeat for `social-river` and `social-permit`, using a fresh output directory per case and round. Replay checks the generator, direction, and HTML before the reviewer runs. The audit verifies that the critic used Playwriter at both widths and that the before and after images match the reviewed build.

```sh
python3 evals/social-design/make_specs.py "$SPECS"
python3 evals/reactions/live_review.py --cells "$CELLS" \
  --benchmark-spec "$SPECS/social-lighting.json" --check-input
python3 evals/reactions/live_review.py --cells "$CELLS" \
  --benchmark-spec "$SPECS/social-lighting.json" --out "$ROUND" \
  --chrome "$CHROME" --playwriter "$PLAYWRITER" \
  --model "$CRITIC_MODEL" --effort low --quota-probe "$QUOTA_PROBE"
python3 evals/reactions/audit_review.py --run "$ROUND" --cells "$CELLS" \
  --benchmark-spec "$SPECS/social-lighting.json"
```

Use the [Playwriter render and live browser setup](../v1/README.md) for additional responsive and reduced-motion checks. Use the same prompt permissions for both arms. To audit the recorded retrieval without generating a page, run `python3 evals/social-design/preflight.py`.

[Source observations and access routes](../../research/SOCIAL-DESIGN.md)
