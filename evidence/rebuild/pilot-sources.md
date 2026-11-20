# Pilot sources: slice C (lane 419b2a67, 2026-11-20)

Fetched headless with `curl`, no login and no GUI. The raw files are in `.context/src_untrusted/` (untracked). "Evidence" means I read the quoted string or viewed the image myself. "Hypothesis" means a design inference I did not test. `palette.contrast` was removed from the JSON; ratios are computed at validation. Receipts for this pass: ink/paper 12.2–17.3. Accent/paper: 9.18, 5.17, 4.67, 5.77, 5.24. Accent/ink: 12.49 (platform-sign).

| Source | SHA-256 (first 16) | Verified observation | Used by |
|---|---|---|---|
| Agrumea Farm hero, `assets.awwwards.com/…/6aacf2ed22405670949235.jpg` | c895e8a31706334d (matches root UI-SOURCES.md) | **Viewed.** The jars are the hero on cream paper with an oxblood blob and orange type on a curved path. The single CTA is a small pill on the featured jar ("Scopri il prodotto") | object-hero |
| Apple MacBook Air `main.built.css` | d337b819f31f9b91 | `.typography-hero-headline` is 64/56/32px at weight 600. `.typography-body` is 17px at -0.022em | object-hero (ratio), platform-sign (body floor) |
| Linear home `linear.app` (server HTML, scripts stripped) | fedc52d4d044bf20 | The product mock shows one focused issue "DRV-8852" with a "1 / 84" queue position, a sidebar of "Inbox \| My issues \| Reviews", and a properties rail "In Progress \| Medium \| Karri": one item in focus, its queue position and its state | exception-first (evidence) |
| Realtime Trains departure board (attempted) | ee923f1b1d973395 | Blocked by a JavaScript bot check ("Just a moment..."), so not used | none |
| GOV.UK button `design-system.service.gov.uk/components/button/` | c6b888bb475a2afe | "Write button text in sentence case, describing the action it performs." | platform-sign, scale-ledger |
| Studio Dado hero, `assets.awwwards.com/…/69a01956b8d34010634085.png` | 37d012d4d92f9972 | **Viewed earlier.** The serif display "FORM FOLLOWS FEELING" is set full-bleed over interior photography, with a small sans nav on an offset grid | field-office |
| Studio D `studiod.nu/en/` | 90fd2feed1c58e0b | HTML contains "eye level throughout the design process" (the "Spatial design at eye level" heading is per root UI-SOURCES.md; my grep matched only the body phrase) | field-office |
| Butterick, line length | d251246ebd7a88b3 | "Aim for an average line length of 45–90 characters, including spaces." | saltline |

**Use with real brief data.** Records are reusable directions: `[bracketed]` slots in `action.label` and `focus` are filled from the brief (product, price, item ID, plan, title). No fixture names, prices or counts appear in the JSON.

**Transferred principles.** Each record carries one.
- object-hero: the product object as the hero, with the CTA attached to it.
- exception-first: the exception gets promoted out of the list.
- platform-sign: signage-scale numerals and an action-named button.
- ground-plane: a serif display over full-bleed material photography.
- scale-ledger: one quantitative scale instead of a grid of identical cards.
- margin-front: a 45–90 character reading measure with print margins.

**Distinctness across the six.**
- Every record has a different display face: Fraunces, Plex Condensed, Archivo Narrow, Instrument Serif, Bricolage Grotesque, Newsreader.
- Every record has a different accent: plum, rust, signal yellow, moss, teal, terracotta.
- Every record has a different skeleton: object split, exception strip, sign band, full-bleed, scale bar, 8/1/3 margin.

**Limits.**
- scale-ledger rests on one source (GOV.UK) and is labelled a house target.
- No imagery is supplied. The fallbacks are CSS or type only.
- All fonts are OFL-1.1 (Google Fonts). Their licences were not re-fetched in this pass.
- No accent is used as body text below 4.5:1. All six accent/paper (or accent/ink) pairs are ≥4.5 after adjustment.

**Revision.** C follow-through: fixture data replaced with slots, ids made generic, motion durations brought within 200–400 ms (ground-plane 600 → 400).
