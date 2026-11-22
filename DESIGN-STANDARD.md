# Standing design principles v2

Apply this standard to web, mobile, and native designs. A distinctive design starts with the subject, the people using it, and the work they need to finish. [Anthropic frontend design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design) · [Apple design principles](https://developer.apple.com/design/human-interface-guidelines/design-principles)

## Art direction before code

Use X and Reddit as the starting point for visual direction. Look for work with strong engagement in relevant communities and specific comments about the design. Open the work itself and identify the choices that earned attention, such as a surprising layout, a precise typographic treatment, or an interaction that makes the subject tangible. Recreate the effect with this brief's content, composition, and original assets. Use research and award galleries to check technical details and trace a reference back to its maker. [Social reference workflow](research/SOCIAL-DESIGN.md#reference-workflow)

Write a short plan stating who uses the design, what matters most, what belongs outside the interface, and how it should feel. Name four to six hex colors and assign their roles. Choose one type family or two clearly distinct families and name their roles. Describe the layout, reading order, primary action, and one memorable detail drawn from the subject's world. Revise the plan if it would fit any similar product without changes.

## Composition, type, and interaction

- Spend the boldest decision on one focal element. Give supporting details a clear order and keep equivalent controls in predictable positions. Remove decoration, redundant copy, and controls that compete with the task.
- Choose type for the brief. Use perceptible weight and size jumps where the hierarchy needs them, including a roughly 3× display-to-body jump when appropriate. Keep body lines below 80 characters and use sentence case for labels.
- Commit to dominant colors and selective accents. Name colors as CSS variables on the web and use native design tokens where appropriate. Use one deliberate motion sequence or a useful response to an action. Respect reduced-motion preferences.
- Preserve every necessary action on narrow screens. Give controls visible keyboard focus and accessible contrast. Use text or shape alongside color for state. Use active, plain copy and one name per action. Buttons name their outcome. Errors identify the problem and the repair. Empty states invite the next useful action.

## Defaults that require a reason

- Inter, Roboto, Arial, Open Sans, Lato, and default system fonts are poor default identities. Treat Space Grotesk with the same caution. Use a platform convention or existing typeface when the brief gives it a specific role.
- Skip purple gradients on white, cream and terracotta, and near-black with a lone acid-green or vermilion accent unless the subject justifies them.
- Avoid interchangeable rounded cards with the same radius and gray shadow, tracked-out uppercase eyebrows, middle-dot metadata strings, tiny monospace data labels, arrows on every control, decorative step numbers, and a single italic or colored headline word used for effect.
- Avoid fade-and-slide entrances on every section and hover transitions on every card. Use a specific visual reason for any exception and examine it in the live design.

## Independent review and delivery

Keep the builder and evaluator separate. Freeze the required screens, viewports, fixtures, tasks, and expected outcomes before coding. Calibrate the skeptical evaluator with three independently scored examples before reviewing the new rubric. Include a polished design with a broken primary action and withhold one example's score until the evaluator grades it. Use unrelated calibration briefs. Give the evaluator the task and an anonymous live build. It opens the build, navigates to the relevant screens, and uses the intended controls before it scores. It records observable results and captures the before and after states. Weight design quality and originality at 30% each, and craft and functionality at 20% each. [Release rubric and calibration](evals/vision/rubric.md) · [Planner and evaluator research](https://www.anthropic.com/engineering/harness-design-long-running-apps)

Run at least five and at most fifteen scored rounds. Rank a build by its lowest required screen score, using the mean as a tiebreaker. Use unrounded scores. A strict improvement over the best resets the miss count and calls for refinement. A tie or loss counts as a miss and calls for an aesthetic pivot if continuing. Starting at round five, stop after two consecutive misses or at round fifteen. Preserve the strongest verified iteration. Use a second blind live evaluator on the exact frozen finalist. Each ballot must independently reach 9.5 on every required screen. Apply the score and functional gates separately from the stopping rule. Show both sets of per-criterion scores, the critique and change history, and the final screenshot. If a gate is open, report the observed result and its limitation.
