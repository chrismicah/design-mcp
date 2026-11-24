# Review F (source challenge): arm D landing, dashboard, mobile

Reviewer: coordinator `eb3116f5`, not the author. Files: `evidence/rebuild/comparison/D/{landing,dashboard,mobile}.html` (byte-identical to `.context/rebuild/candidate/D/`). Method: scripted source scan plus the script block, reduced-motion block and button markup of each. Skimmed `remaining-qa.md` and `held-out-findings.md`.
**No visual verification was performed.** Nothing was rendered; computed fonts, overflow, contrast in place and focus visibility are unverified. This receipt does not satisfy, replace or relax any rendered criterion.

## Verdict: source is sound on action, focus and reduced motion. One blocking defect: the fonts cannot load.

**F1 (blocking, all three). Named faces are declared but never loaded.** Each file sets `--display` and `--body` to the direction's faces and contains no font `<link>`, `@import` or `@font-face`. On a machine without those faces installed, landing falls back to Georgia and `system-ui`; dashboard and mobile fall back to `system-ui` for both roles. That is a banned visible brand font and a single-face page. A first-family static check passes these files, so only a computed-font check at render can decide this. Until then the font criterion is **not met**, not "pending pass".
Likely cause: the experiment's "self-contained file" rule. Decide once, for every arm equally: allow a font link, or embed. `direct` should return the loading instruction with the faces.

| File | Finding |
|---|---|
| landing | **F2.** `#notice` and `#count` update on click with no live region; the result of the primary action is silent to a screen reader. **F3.** `.buy` is `position:sticky;bottom:0` with no safe-area inset; on a phone it can sit under the home indicator and can cover a focused element |
| dashboard | **F4.** The toggle sets `aria-pressed` and also changes its label to "Show all loads", so the pressed state reads as the opposite action. Use one mechanism. **F5.** Focus mode hides `tbody tr:not(:first-child)`: it keeps whichever row is first, not the delayed load. **F6.** One `<table>`, one breakpoint at 700 px, no horizontal scroll container: likely overflow at 390 px. **F7.** The heading is both a polite live region and focusable; if the script also moves focus there it announces twice (script tail not read) |
| mobile | **F8.** The reveal is announced by `aria-expanded` and sits beside a live region; check for double announcement. No breakpoints and no safe-area or dynamic-viewport units; plausible for one column, unverified |

## Confirmed from source

- Primary action is a native `<button>` with a working handler in all three; Enter and Space work without extra code. No click handlers on non-interactive elements, no `href="#"`.
- One global `:focus-visible` rule (2 px ink outline, 3 px offset, paper halo); no `outline:none`. This replaces the `currentColor` ring I flagged earlier.
- `prefers-reduced-motion` disables all animation and transition; no script-driven animation exists. Durations are 240 ms and 280 ms.
- Controls declare a 44 px minimum height; `lang`, viewport, `<main>` and one `<h1>` are present. No backdrop blur.

## Limits and process notes

- Each file is 3,300–4,000 characters. These are single-screen sketches; comparing them with award sites will mostly measure how little is there. Check that the other arms are of similar size.
- I did not read arms N, L or C. If none of them load fonts either, F1 is an experiment defect shared by every arm rather than a D defect, and no arm can claim a type advantage.
- `held-out-findings.md` shows a held-out miss fixed by adding intent phrases. That brief is no longer held out; a fresh one is needed after each such fix, and phrase lists will keep missing new wording.
- Landing contains two `gradient` declarations I did not inspect.
- Rollout criteria are unchanged. The leased capture at 1440 and 390 in `remaining-qa.md` step 2 remains required before G.
