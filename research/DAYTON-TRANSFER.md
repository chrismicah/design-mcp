# Dayton consultation holdout

Use the frozen Dayton brief and the exact consultation direction returned by
the four verified installs of d2ad739. Record the first generated draft before
supplying screen measurements. Keep the draft blind to the Tacoma outcome.
The user needs to identify the practitioner, both visit options, office hours
and call target. The note stays local. The viewport contract applies at
320 × 700, 390 × 844 and 1440 × 900. Require the name and preview at the
opening, the actual phone link, a keyboard-selected running assessment, a
visible missing-name recovery, an editable result and clear local-only status.

The primary comparison is to the acceptance contract. Only if the fresh draft
misses the opening with the rest of the task intact, freeze it as a parent for
an ordinary repair and a measured repair. If the page repeats choices, test the
browser-derived overlap as a concrete deletion suggestion, with the same
brief and frozen page in both arms. Treat the original and both revisions as
distinct artifacts. A healthy fresh draft is a successful transfer for this
fixture. It provides no positive evidence for adding measured feedback.

## Sources for the next repair

The clinic owner’s Reddit critique thread surfaces three observed problems:
phone information moved while people tried to read it, overlapping copy slowed
scanning, and an appointment label opened a generic contact page. Use those
observations to test static contact facts, one clear label per action, and
whether extra service copy answers a distinct question. The discussion is
archived, its engagement count was unavailable in the read, and its linked live
site returned 502. [Clinic design critique](https://www.reddit.com/r/UXDesign/comments/1lsrqk8/)

GOV.UK’s radios guidance uses a meaningful group label for a single-choice
task. Reuse that accessible label as the visual service prompt whenever it
already names both options. Preserve extra service explanations when the
brief gives visitors a separate decision to make. This is an inference for
the consultation fixture. [Radios](https://design-system.service.gov.uk/components/radios/)

X’s engineering report pairs exact render replay with a separate cold-network
comparison. The practical check for local-only consultation pages is to
confirm the phone action and office facts are available with web fonts delayed
before the screenshot waits for the final type. Keep that readiness result
separate from a full-font visual review. [X engineering write-up](https://blog.x.com/en/engineering/rebuilding-the-global-town-square-from-scratch)

## Replay parity

The new fixture-driven replay preserved every check result on the nine archived
Tacoma drafts at 320, 390 and 1440 px. All exact HTML hashes and every new
capture hash verified against the browser artifact. The eligible controls
remained eligible and the measured repair still missed the 320 px opening
preview. Dayton is a separate test with its own receipt. [Parity receipt](../evidence/benchmark-v1/practice-fixtures-replay-parity.json) · [Browser run](https://github.com/chrismicah/design-mcp/actions/runs/45283273090)

## Unedited result and focus experiment

The first draft generated in 45.74 seconds with 2,314 output tokens. It used a
single service picker. The phone action, office facts and preview were visible
at all three widths. The preview bottom was 600.1 px at both phone widths and
462.6 px on desktop. Keyboard selection, blank-name recovery and note editing
worked with zero post-load requests. The note appeared fully in the first
frame. Focus landed on its surrounding section and missed the separate focus
check at all three widths.

The first harness tied geometry and editing to successful result focus. Its
replay of the same HTML now attempts each check independently. The original
receipt is preserved. This checker correction did not change any Tacoma
candidate’s eligibility. The next diagnostic changes only the target of the
successful focus call to the editable note. Keep the frozen layout, motion and
data handling. Restore the named result on all widths before awarding a pass.
[Installed and browser evidence](../evidence/benchmark-v1/dayton-initial-browser.json) · [Independent browser checks](https://github.com/chrismicah/design-mcp/actions/runs/45284349587)
