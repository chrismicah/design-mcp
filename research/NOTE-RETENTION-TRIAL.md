# Editable consultation note retention trial

A visitor preparing to speak to a named professional may improve a
first sentence, return to check the visit and reopen the result. The
authored Albany model demonstrated a loss on that journey. Its revised
draft retained the visitor's own sentence at desktop and phone sizes.
The visual series closed with a weaker-screen high of 8.20. This
trial isolates the functional guidance and leaves visual design choices
to matched generation.
[Blind Albany replay](https://github.com/chrismicah/design-mcp/blob/cf4369125c0ec6e3062e7b3e4aed2fb5d2cdf871/evidence/benchmark-v1/albany-call-slip-integrated-blind.json)

Compare the installed direct-consultation direction against 9976ef1.
Change one field. Keep the local disclosure, named first-frame focus,
caller facts and visual brief fixed. Verify that all 48 frozen
unhinted control replies are identical to the baseline. Keep explicit
form overrides identical. A new patient preparing for a first dental
call supplies a held-out brief with no direct request to preserve
edited text. A separate practice brief must pass the same workflow
before promotion, with both arms built by the same model and prompt
prefix at equal effort. At 320, 390 and 1440 px, type an identifying
sentence, return and reopen. The edited sentence must be identical.
A new visit must produce the new visit's text and keep the recognized
name. Zero post-load requests and no URL changes are required. A
different behavior or visual drift in retained controls warrants
another inspection before promoting the field.

## Held-out routing defect

The frozen first dental call says it does not book an appointment.
Both control and the guidance-only trial selected service-work-order.
The dentist and appointment tags tied and the work-order record came
first. Adding a second dentistry tag changed the result during a
diagnostic probe, but the held-out brief remains verbatim. A separate
commit excludes a negated appointment phrase from consultation
ranking. That exclusion applies only when landing and contact intent
are both present. Genuine appointment requests and explicit form
overrides are controls. Keep the previous routing miss in the receipt.

The combined candidate bd1e7aa passed 75 direction tests. Source stdio
returned the same 48 frozen replies, five form overrides, and genuine
booking control. Only the intended action field changed for four
existing practice routes. The untouched dental brief changed from
service-work-order to direct-consultation. This source comparison
awaits clean-install parity and a test that the guidance
transfers through generation.
[Exact source stdio replies](../evidence/benchmark-v1/note-retention-source-stdio.json)
