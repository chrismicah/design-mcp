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
