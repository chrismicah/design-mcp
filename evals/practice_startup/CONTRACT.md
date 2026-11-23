# Practice first paint under a held font stylesheet

Test two archived consultation pages at 390 × 844. Keep exact source and the
same browser. In one arm retain the original remote font stylesheet. In the
other, defer that same stylesheet with a print media query and enable it on
load. Include a normal stylesheet fallback for browsers with scripting off.
Leave the CSS, page content, script, and font request URL as supplied.

Intercept the single font stylesheet in both arms and hold it until after
measurement. Serve an empty stylesheet at release so the loading experiment
has a reproducible dependency and makes no request to the public font host.
While that resource is still pending, require observed first contentful
paint, the heading and call link within the opening viewport, and real Tab
navigation to the call link. Record timings and save a normal post-release
image. If the controlled test shows a win, run a second check with the actual
font stylesheet before promoting guidance. This fixture has inline site CSS.
The result does not rank font providers, assert a live network speed, or
replace visual taste or final rendered layout checks.

## Verified outcome

With the stylesheet held for 500 ms after the heading and phone link entered
the DOM, both deferred pages painted and accepted Tab focus on the call link
before release. The controls painted after release. In the live-font rerun,
Dayton’s first contentful paint moved from 708 ms to 52 ms and Tacoma’s from
624 ms to 60 ms. Both original fonts loaded. Each fixture’s two settled
390 × 844 PNGs matched byte for byte, including the call link’s focus state.
The run also repeated the existing consultation journeys.

This evidence covers two pages with inline site CSS, one phone viewport and
an imposed delay. Keep the authored variants on the verification branch.
Adopt any wider font-loading guidance after a matched generated case confirms
the first-view behavior and preserves the final layout. The staged Madison
result-focus comparison remains a separate test.
[Comparison and capture digests](../../evidence/benchmark-v1/practice-font-startup.json) · [Hosted playback](https://github.com/chrismicah/design-mcp/actions/runs/45287604824)
