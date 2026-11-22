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

Run `python3 evals/social-design/status.py` after saving an audited ballot. The report ranks each candidate by its weaker viewport and uses the mean to break a tie. It checks the archived control and critic session for each round, and reports the score floor and the standing stopping rule separately.

Freeze the strongest build and its control for the second critic. Run the same live commands with a new `ROUND` directory and a separate calibrated vision session. Keep the first ballot and the round history out of the second session's context. Save both results. `status.py` reads an archived confirmation named `social-CASE-confirmation-rN.json` for the strongest round. To check a new audit before archiving, pass `--lighting-confirmation PATH` or `--river-confirmation PATH`. Confirmation requires distinct live evidence for the same two builds. Both ballots must reach 9.5 on each viewport, beat the control, improve originality and preserve usability. A lower score goes back to the builder with the critic's specific repair. After two non-improvements once five rounds have been scored, or after 15 scored rounds, close the series and record a distinct premise before continuing.

For a targeted draft repair, copy the original matched cells and place the revised HTML in the copied `social/repair.html`. Keep the original generation files. Set `draft_repair` in a copy of the private spec with the two SHA-256 digests under `original_sha256` and `repair_sha256`. The live runner replays the original generation and serves the exact anonymous parent and repair at both widths. Store the result separately from the retrieval benchmark. A distinct evaluator session remains mandatory when both versions share one author.

[Source observations and access routes](../../research/SOCIAL-DESIGN.md)

### Lighting, round 2

The first blind critic found the existing catalog's human-scale scene easier to read. The revised portfolio should make a producer feel like they are watching a cue called from the wings. Use one proscenium view with a performer and shadow at the same scale in every cue. In the wings, a visible lighting source shows which direction the light comes from. Keep the cue controls and the current technique on the same rail. Remove the abstract sphere, plinth and detached status panel. Warm-black `#211C23` frames the stage, lilac-gray `#E7DDE9` supports the reading surface, and plum `#703E62` selects the cue. Amber `#E8AD54` and ice blue `#91C2E8` belong to the supplied stage states. Bricolage Grotesque names the show and cues. IBM Plex Sans sets the technique notes. Let the shape of the performer's shadow tell the story before the notes do.

### River, round 2

Keep the cross-section that won the first blind comparison. A resident should be able to read the current elevation and closures from arm's length. Make the selected level the one large number and give the map a short caption. On phones, label each place in readable text below the scene and use shape markers to connect it to the bank. Omit miniature diagram labels on mobile. Keep the same navy, blue-gray, deep teal, slate and gold palette and Barlow Condensed with Source Sans 3. The waterline should meet the selected mark in the same state that the closures change.

### Lighting, round 3

Round 2 made the light change legible and earned the critic's preference for the task. The visual grades still favored the control. Make the producer feel like they are looking through the wings during a dress rehearsal. Put a small identity stripe above a cinematic stage, and give the cue inspector a separate reading column on wide screens. On mobile, keep the full action and the cue instructions close to the scene. The single focal image is a dancer mid-reach with a shadow that continues the gesture. Omit the stock standing figure, oversized header, and tiny technical legends. Use dark plum `#241C2F` for text, rose-gray `#F1E7EB` for paper, plum `#753966` for active controls, and two lamp tones `#FFC36C` and `#92B7FF` when the brief calls for them. Use Fraunces for the identity and IBM Plex Sans for controls and technique.

### River, round 3

The mobile cleanup in round 2 left the crossings hard to tell apart. Change the scene to an annotated flood chart a resident could read on a noticeboard. Three labeled contour lines run across a single section. Draw a small path, ferry and footbridge icon at their actual labeled thresholds. Keep the text labels as readable HTML along the contours at both widths. The waterline crosses the markers and changes the closure list in the same frame. Leave out scale figures that repeat the labeled thresholds and decorative topography. Use blue-black `#172B44` for text, pale gray-blue `#EFF4F7` for paper, saturated navy `#204D8C` for water and the chosen level, soft blue `#A4CBE7` for unreached contour space, and ochre `#EFBE61` for marked closures. Use Archivo Narrow for elevation labels and IBM Plex Sans for the list and controls.

### Lighting, round 4

Keep round 3's dress-rehearsal composition. Fit the full stage and cue inspector inside the first 900 CSS px at desktop width by making the header a short horizontal line. Leave the most room for the performer and the visible shadow. At 390 px, bring the actor's gesture and shadow tip closer together in the framed view, and give the shadow strong contrast. Use all five round 3 colors and the Fraunces and IBM Plex Sans pairing.

### River, round 4

Keep the readable contours from round 3 and bring the answer above the chart on phones. The resident sees the current level, the level choices, and the full closure list before needing to scroll. A compact 240–300 px section below shows why those places close. Keep the same five colors and type pairing. Use blue space around the current reading and keep the ochre markers attached to the crossed contours.

### Lighting, round 5

Keep the room, compact masthead, and expressive performer from round 4. Give the selected cue a persistent plum fill and a small circular lamp marker so the producer can see the selection after tabbing away. Use the existing light paper for its label and a separate focus outline on every control. Let the stage remain the most prominent part of the page.

### River, round 5

Keep the result and level choices above the compact mobile chart. Give the resident a more recognizable view of the bank. Use three small original illustrations with unmistakable physical relationships: a footpath cut into the low bank, a ferry beside its landing at the middle mark, and a footbridge spanning the water at the upper mark. Connect each readable label to the place with a short line. Use the same five round 3 colors, with dark silhouettes over the pale channel. Keep Archivo Narrow for level readings and IBM Plex Sans for the place labels and controls.

The first round 5 capture exceeded the client transport limit on two desktop images. The full PNGs were saved locally, but the client trace contained truncated images. That ballot is ineligible. Rerun the same direction with flat washes, folds and shaped shadows so the full-size pixels fit the transport budget. Keep the color and type roles from round 5.

### River, round 6

The resident still gets the answer first. Create the feel of an illustrated river field sheet with one continuous bank cutaway and a thick waterline running across the page. Make the elevation the anchor on the report edge and echo it on the waterline. Use large, distinctive silhouettes for the path, ferry and bridge. Simplify the terrain fill and keep the title short. Deep tide `#163759` carries the ink, pale sky `#EDF4F6` the paper, ultramarine `#254D9C` the active reading, clear blue `#9BC7DF` the water, and signal ochre `#EABB62` the closed markers. Use Archivo Narrow for the elevation and IBM Plex Sans for the plain-text outcome. Keep the same supplied facts.

### Lighting, round 6

One bounded Astra planning pass proposed the moment a stage crew tests the light on a half-open curtain. A producer switches the three cues and watches the same folds and turned hem catch light differently. Leave out the figure and keep the curtain as the focal point. Use stage charcoal `#191C20`, curtain slate `#626B74`, paper white `#F5F3EB`, lamp amber `#E8A348`, and backlight blue `#508BFF`. Barlow Condensed sets the identity and cues. Barlow sets the technique. Use a 960 × 420 scene at desktop width and a 358 × 300 scene at 390 px. Put the named choices and selected technique together directly under the light. Before accepting, switch all three cues by keyboard at both widths and confirm the lit hem, focus, selected cue and matching technique fit together.

### River, round 7

Round 6 crowded the mobile chart. Try a bolder field graphic with three oversized crossing silhouettes on a stepped bank. Put large HTML names on a separate label rail aligned to the steps. Keep the real level control and complete result directly above the mobile graphic. The only moving reading is the colored waterline. Use deep-water ink `#092538`, pale paper `#EBF5F6`, cobalt `#2053A6` for the active reading, teal `#61BCD4` for water, and gold `#F2C35E` beside named closures. Use Archivo Narrow for the level and IBM Plex Sans for terms and controls. Keep the illustration clear of any tiny labels or terrain texture.

### Lighting, new direction

A theatre producer should feel like they have a hand on the lighting console. Make one illuminated calibration object the centerpiece of an optical bench. Use a shallow, folded metal screen whose three broad faces respond differently to each cue. Keep the object and floor in view on mobile. Align a full-width row of three cue keys to the bench and use the whole width of the same row for the selected technique beneath it. Omit the performer, curtain, ornamental technical markings and biography. Use ink violet `#252140`, cool paper `#E1E5F1`, lens silver `#A8AEC8`, tungsten `#F6B96B` and cobalt `#2A54B7`. Use Bricolage Grotesque for the identity and cues and IBM Plex Sans for the technique. The broad metal fold should catch light in a physically plausible way that a producer can read immediately. Check that each cue changes the object and written technique together and remains identifiable after focus moves.

For the second optical bench round, turn the abstract light study into a human-scale rehearsal. Keep the full-width cue keys and their selected technique. Give a single performer an asymmetrical reach toward the light and let the shadow extend the gesture onto the floor. Use the folded screen as the rear plane and keep enough empty floor in the phone frame to read the shadow. Keep the five colors and both type roles. Remove any repeated cue language or reference legend.

### River, new direction

A resident should get a clear, quick reading, with the physical landmarks making the thresholds memorable. Compose one wide floodwall scene with a large stenciled height gauge where the water meets it. Let the water visibly cover the lowest marks and change the way each crossing is drawn as it closes. Keep a single complete status sentence next to the controls and fit it before the scene on mobile. Leave out the separate label rail, map legend and inset detail panels. Use deep slate `#132E36`, limestone `#E9E5D8`, tidal green `#176167`, wet stone `#7FABB2` and brass `#E0AC44`. Set the elevation and title in Archivo Black and the controls and closure language in IBM Plex Sans. The gauge and landmarks should feel like part of the same physical waterfront. Test 6 m, 2 m and the transition between them with the same facts and unmistakable focus.

For the second floodwall round, keep the palette and type roles. Set a maximum desktop art height of 415 px and keep the complete scene, controls and outcome in the first viewport. Draw the phone scene as a distinct composition around the wall and water. Put the gauge values in large, responsive HTML aligned to the paint markings. Show the stopped ferry floating at its landing in the high-water state. Leave out micro-labels drawn into the artwork and repeated place names.
