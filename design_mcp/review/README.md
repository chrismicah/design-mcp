# Page review

Scan a web page, get the first thing to fix, and see the change on the page's own pixels. Everything runs on this computer. Nothing is uploaded.

**Status: written, not yet run.** The session that wrote this branch could not execute Python, Node or a browser. The tests below have not been run, and no speed number has been measured. Treat every instruction here as intended behavior until the check command passes.

## Three ways in

| Start from | Do this | What happens |
| --- | --- | --- |
| The page you are on | Click the toolbar button, then **Review this page** | The extension reads what is visible in that tab, blanks out fields in the picture and hands the capture to the local reviewer |
| A pasted address | Paste it in the popup and press **Open**, or run `design-mcp review example.com/status` | The public page opens in a tab. You start the scan there with the toolbar button |
| A pasted address, no extension | `design-mcp review example.com/status --playwriter PATH` | The page is captured at 1440 × 900 and 390 × 844 in a separate Chrome with a new empty profile |

Each route produces the same capture format and goes through the same steps: scrub, three local checks, one finding, one preview file.

## Set up the extension

```bash
design-mcp review --extension-path
```

Open `chrome://extensions`, turn on Developer mode, choose **Load unpacked** and pick the folder that command prints. Click the toolbar button on any web page and press **Review this page**. The first time, the popup shows one command with this copy's ID filled in:

```bash
design-mcp review --install-host <extension id>
```

That writes two files: Chrome's host manifest for `com.design_mcp.review`, and a launcher that starts the reviewer for that one extension. `--dry-run` prints both paths without writing. `--uninstall-host` removes them.

## What the first result contains

The finding names the region, the problem, one change and a check you can run. For the hand-written test capture the problem line is expected to read:

> “2 of 2 rooms” is hard to read at 390 px wide: its text color #9aa0a6 on #f6f5f1 measures 2.4 to 1, and text this size needs at least 4.5 to 1.

The change line names the exact replacement color: the nearest darker or lighter shade of the current one that reaches 4.5 to 1. The check line states the contrast to measure afterwards. This example is test input worked out by hand, not a recorded page.

The preview file shows the capture with the region outlined and one **Before / After** control. After recolors the captured text pixels of that region, so the glyphs are the page's own. The file has no scripts, loads nothing from the network, and allows only its own embedded picture and one hash-pinned style sheet.

Local checks, most blocking first:

1. A fixed or sticky layer on top of the main button
2. Sideways scroll of more than 1 CSS pixel
3. Text under 4.5 to 1 on a flat fill (large text is exempt)

Only the contrast finding has an after view. For the other two the preview says so and shows the outlined capture. A visual review by a model is not part of this build. The result says "not run" and never substitutes an invented answer.

## What is kept and what is removed

- Kept per region: role, name, landmark, nearest heading, short locator, reading order, box as fractions of the view, font family, size and weight, text color, fill color, whether the fill is flat, pressed and disabled state. At most 8 regions per view. Missing values are stored as `unknown`.
- Removed before anything is stored: sign-in details in the address, credential-like query values, everything after `#`, `data:` and `file:` addresses, typed field values, and PNG text chunks. Fields, editable areas and embedded frames are painted over in the picture.
- Refused outright: pages that are not http or https, captures nobody started, captures with fields that were not blanked out, and oversized or malformed input.
- Results go to a private folder in your user directory (`~/Library/Application Support/design-mcp/reviews` on macOS). The newest 20 are kept.

The extension asks for `activeTab`, `scripting` and `nativeMessaging`. It has no host permissions, no content scripts, no background worker, and its pages cannot make network requests. The local reviewer opens no port. It serves one request from one pinned extension origin, refuses requests over 24 MiB before reading them, and keeps replies under 512 KiB.

## Check command

Standard library only, from the repository root:

```bash
python -m unittest tests.test_review -v
```

With the project's test dependencies, as part of the full suite:

```bash
python -m pytest tests/test_review.py -q
python -m pytest tests
```

Replay the saved-capture route once the tests pass:

```bash
design-mcp review --evidence capture.json --out ./review-out
```

## Browser verification still to do

These need a browser and are the acceptance steps for this slice. None has been done.

1. Load the unpacked extension. Confirm the popup paints one primary button and that DevTools shows no network request before the button is pressed.
2. On a public status board at 1440 and 390 wide: press **Review this page**. Confirm the finding names a real region, the popup crop shows that region outlined, and the preview's outline sits on it.
3. In the preview: Tab to the Before / After control, switch with the arrow keys, confirm the focus ring and that only the outlined text changes color. Confirm DevTools shows no blocked style sheet (the hash must match) and no network request.
4. Seed a value in a text field, scan, and confirm the field is a flat gray block in the preview and the value appears in neither stored file.
5. Error paths: `chrome://extensions`, a PDF, the extension store, switching tabs mid-scan, scrolling mid-scan, the host not installed, the host installed for a different ID.
6. `--playwriter` capture of one public page under the render lease. Confirm two views, blanked fields and separate load and capture timings.
7. Speed: open the popup 30 times and scan 30 times on the reference Mac, then read `localStorage['dm.timings']` in the popup's DevTools. Report p95 for open (target under 200 ms) and scan (target under 1.5 s) with hardware, source pin and fail count.

## Known gaps

- The blind visual critique gate (9.5 of 10) has not been attempted. No screenshot of this UI exists yet, so no score is claimed.
- No model review, no redesign builder, and no after view for layout findings. The first finding comes from three local checks only.
- The extension has not been loaded in Chrome. Two behaviors need confirming there: opening the saved preview through a `file://` address from the popup, and SVG filter rendering of the after view.
- The `--playwriter` route follows `evals/v1/render.py` but has not been run. Requests to private addresses are blocked by address pattern; a public page that names a private host through DNS is not blocked.
- No keyboard activation is performed on a live page, so the interaction part of the capture format is validated but never produced.
- The 8 reported regions are chosen by the collector: first heading, main button, up to three hardest-to-read lines, first status, then reading order. That choice has not been checked against human labels.
- Host setup covers Chrome on macOS and Linux. The unpacked extension has no icon and no fixed ID, so the ID must be passed once.
- Font family is the first family in the computed stack, which may differ from the face actually drawn.
