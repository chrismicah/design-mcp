# Review: slice C pilot directions

Reviewer: coordinator `eb3116f5` (Claude Fable 5.2); author was lane `419b2a67` (Claude Opus 5.5). Same model family, different session. Read-only.
Read: every record's `type`, `palette`, `motion`, `action`, `sources`, `credit`, `tags`, and the first 230 characters of `why`; `layout` and `imagery` for `cinder-object-hero` only; the source table in `pilot-sources.md`.
**Not checked:** `layout` and `imagery` for five records, font licences against their publishers, any rendered output.
Recomputed independently: all 12 claimed contrast ratios (WCAG relative luminance). All match the records to two decimals.

## Overall: 0 of 6 accepted as reusable directions. 5 revise, 1 rework.

The craft inside each record is specific and the contrast claims are true. The blockers are structural and shared.

**X1. These are answers to the six test briefs, not directions.** Ids, titles, tags, focus, imagery and button labels carry the fictional facts: "Add Alto Carmo, 250 g — $19", "Focus LS-057 at Bay 4", "Show ticket TKT-0837", "Open the Mill Race case study", "Continue with Team — $28/month", "Read The Coast at Low Tide". Two consequences:
- Served to any other coffee, freight or magazine brief, `direct` would return another company's product, price and ticket number.
- Arm D would be scored on the same briefs the records were written for. That measures recall, not generalisation. Held-out briefs are required before any claim.

Fix: split each record into a direction with slots (`{product}`, `{unit}`, `{price}`, `{primary_object}`) and a separate worked example. Tags describe the situation ("single physical product, first-time buyer"), not the industry.

**X2. The six converge.** 6 of 6 are light mode on warm off-white paper (`#f3ebe0`, `#eef0ec`, `#f7f5ef`, `#e9e6dc`, `#fbfaf7`, `#efe9dc`) with near-black ink. Two accents are the same burnt orange (hue 18 and 15). Atkinson Hyperlegible is the body face in two. This is a new house style forming. At least one dark and one cool-paper direction are needed before the convergence measure means anything.

**X3. Accessibility fields are incomplete in all six.** No text colour is given for the filled primary button, no focus indicator, no easing, no keyboard path for the motion trigger. Licence is one string for two faces with no receipt in `pilot-sources.md`.

## Per direction

| Direction | Verdict | Blockers |
|---|---|---|
| `cinder-object-hero` | Revise | X1. Palette (cream paper, oxblood-plum accent) sits close to the Agrumea still it cites (cream paper, oxblood shape): transfer the principle, change the colours. Ratio 4.0 is cited to Apple, whose values give 64/17 = 3.76; label it a house target. Ink on accent is 1.59, so state that button text is paper (9.18) |
| `linehaul-exception-first` | **Rework** | X1. No verified source: the only citation is Linear's home page at strength `hypothesis`, and "My issues" does not support exception-first. Credit names "Linear Orbit", which no receipt covers. The exception is carried by the accent alone; a status needs a non-colour cue. "Pulses once" on every delay change will repeat on a live board: add a rate limit and a polite live region. Display and body are one superfamily at the 2.5 minimum |
| `spur-signal-ticket` | Revise | X1. Accent `#ffcc00` on paper is 1.39: it may only be a fill under ink (12.49), never text, icon or outline on paper; say so in the record. "Signage-scale numerals" has no source; mark it `hypothesis`. Evidence is a 390 px web viewport, not a phone |
| `field-office-ground-plane` | Revise | X1. Credit joins "Studio Dado" and "Studio D"; confirm whether these are one studio or two and cite each separately. The Studio D quote is body copy, not a design observation. Display serif at weight 400, tracking −0.04, over full-bleed photography has no legibility rule; nothing states how text stays readable without darkening the image. Motion is 600 ms and scroll-triggered: allowed once as the signature, but the record must say once per page. Accent on paper is 4.67, marginal on any tint |
| `relay-hours-ledger` | Revise (closest to passing) | X1. The one source (GOV.UK button text) supports the label only; the hours-scale idea is unsourced and should be marked `house target` in `sources`, not just in `credit` |
| `saltline-low-tide` | Revise | X1. The only motion is a hover underline, which does not exist on touch; at 390 px this is the banned "no motion at all". Newsreader with Source Serif 4 pairs two similar text serifs and leaves no face for captions and controls. One source, for line length only. Accent duplicates Linehaul's hue |

## What is sound

- Every claimed contrast ratio reproduces.
- All six name a display and body face with ratio and tracking inside the house ranges, and every motion has a reduced-motion equivalent.
- Button labels name the object and the result.
- Source hashes for the Agrumea still match the root receipt; strength labels are present on every source.
