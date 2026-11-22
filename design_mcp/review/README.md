# Page review

The Chrome extension and review CLI scan a page locally and show the first measured issue. The optional MCP tool sends the captured image and layout facts to your connected client for visual critique.

The installed CLI captured the USWDS address form at desktop and mobile widths through Playwriter. Both views retained the masked Street address field in the eight-region context. On the reference Mac, GPT Computer Use exercised Chrome's missing-host recovery, switched to After by keyboard, and reopened the same preview. [Installed URL run](../../evidence/benchmark-v1/isolated-url-session-e1cd4eb.json) · [Reference Mac walkthrough](../../evidence/benchmark-v1/reference-mac-chrome-f17bd6f.json)

## Three ways in

| Start from | Do this | What happens |
| --- | --- | --- |
| The page you are on | Click the toolbar button, then **Review this page** | The extension reads what is visible in that tab, blanks out fields in the picture and hands the capture to the local reviewer |
| A pasted address | Paste it in the popup and press **Review URL** | A Design MCP tab runs the scan and shows the result. Chrome captures a 1440 × 900 viewport with an empty profile |
| A pasted address, no extension | `design-mcp review example.com/status --playwriter` | The page is captured at 1440 × 900 and 390 × 844 in a separate Chrome with a new empty profile |

The extension's **Review URL** uses the local reviewer and the standard Chrome installation. For the CLI's two-width Playwriter route, install Playwriter 0.12.0 on PATH or supply its executable after `--playwriter`. Add `--no-open` to the CLI command to preview its intent. [Pinned Playwriter MCP guide](https://github.com/remorses/playwriter/blob/playwriter%400.12.0/MCP.md)

Pasted-URL capture checks the resolved address before opening each browser TCP connection. The first hostname stays pinned to its checked address, and assets on other hosts go through the same address check. Hosted Chrome refused an owned loopback fixture both by IP and by a test name that resolved to that IP. Use the toolbar for pages you already have open on a private network. [Browser proof](../../evidence/benchmark-v1/browser-public-network-7bccfc1.json)

Each local route produces a scrubbed capture, runs three checks and saves a preview with the first finding.

## Visual critique and a live task

Install from the current development checkout, which includes `review_page`. In your MCP client config, change the Design MCP server's arguments to `["serve", "--review"]` and reconnect the server. Select a model and client that can see image attachments returned by MCP. Configure Playwriter in the same client for browser input. [Client setup](../../README.md#install) · [Connect Playwriter](../../evals/v1/README.md#connect-playwriter)

Give your agent a URL and one visitor task. For example:

> Review https://designsystem.digital.gov/templates/form-templates/address-form/ at mobile width. Use the Design MCP screenshot to identify the strongest and weakest parts of the form hierarchy. In Playwriter, try reaching Street address with the keyboard. Report where focus goes and whether it is visible. Show the relevant screenshot for each finding.

`review_page` uses disposable Chrome to return one image and the measurements for the opening screen. Playwriter lets the agent navigate, press keys and capture each state in a connected browser. For a local site, have the agent open the connected test tab through Playwriter and capture the page there. The agent uses the screenshot for visual observations and the browser action and resulting state for usability claims.

The Chrome popup itself runs local checks. Use the agent chat for visual critique and a live task walkthrough. If your agent uses a hosted model, its provider receives the image and layout facts returned by the MCP. The MCP masks captured form fields, editable regions and embedded frames.

## Set up the extension

```bash
design-mcp review --extension-path
```

Open `chrome://extensions`, turn on Developer mode, choose **Load unpacked** and pick the folder that command prints. Click the toolbar button on any web page and press **Review this page**. The first time, the popup shows one command with this copy's ID filled in:

```bash
design-mcp review --install-host <extension id>
```

That writes two files: Chrome's host manifest for `com.design_mcp.review`, and a launcher that starts the reviewer for that one extension. `--dry-run` prints both paths without writing. `--uninstall-host` removes them.

If Chrome was launched with a custom `--user-data-dir`, add `--chrome-user-data-dir` with that directory's absolute path when installing or removing the host. Each directory keeps its own launcher, allowed extension ID, and preview history. Run the installation command again to update an existing custom launcher.

## What the first result contains

The finding names the region, the problem, one change and a check you can run. For the hand-written test capture the problem line is expected to read:

> “2 of 2 rooms” is hard to read at 390 px wide: its text color #9aa0a6 on #f6f5f1 measures 2.4 to 1, and text this size needs at least 4.5 to 1.

The change line names the exact replacement color: the nearest darker or lighter shade of the current one that reaches 4.5 to 1. The check line states the contrast to measure afterwards. This example is test input worked out by hand, not a recorded page.

The preview file shows the capture with the region outlined and one **Before / After** control. After recolors the captured text pixels of that region, so the glyphs are the page's own. The file has no scripts, loads nothing from the network, and allows only its own embedded picture and one hash-pinned style sheet.

Local checks, most blocking first:

1. A fixed or sticky layer on top of the main button
2. Sideways scroll of more than 1 CSS pixel
3. Text on a flat fill below 4.5 to 1, or below 3 to 1 when it is at least 24 CSS px or 14 pt and bold. [WCAG contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)

Only the contrast finding has an after view. The other two show the outlined capture. The preview reports whether a model review ran.

## What is kept and what is removed

- Kept per region: role, name, landmark, nearest heading, short locator, reading order, box as fractions of the view, font family, size and weight, text color, fill color, whether the fill is flat, pressed and disabled state. At most 8 regions per view. Missing values are stored as `unknown`.
- Removed before anything is stored: sign-in details in the address, credential-like query values, everything after `#`, `data:` and `file:` addresses, typed field values, and PNG text chunks. Fields, editable areas and embedded frames are painted over in the picture.
- Refused outright: pages that are not http or https, captures nobody started, captures with fields that were not blanked out, and oversized or malformed input.
- Results go to a private folder in your user directory (`~/Library/Application Support/design-mcp/reviews` on macOS). A host installed with `--chrome-user-data-dir` saves under `Design MCP/reviews` in that directory. The newest 20 are kept in each history.

The extension uses `activeTab`, `scripting`, `nativeMessaging`, and in-memory `storage` to hand a pasted link to the review tab. It has no site-wide permissions, content scripts, or background worker. For a pasted link, the local reviewer uses a temporary Chrome profile and loopback-only proxy and debugger. The host serves one request from the pinned extension origin, refuses requests over 24 MiB, and keeps replies under 512 KiB.

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

Review a collector's input capture once the tests pass. The input JSON must contain its screenshot. The output folder puts the image in `preview.html` and saves geometry separately in `evidence.json`.

```bash
design-mcp review --evidence capture.json --out ./review-out
```

## Reference Mac verification

Repeat the installed browser acceptance steps on the reference Mac.

1. Load the unpacked extension. Confirm the popup paints one primary button and that DevTools shows no network request before the button is pressed.
2. On a public status board at 1440 and 390 wide: press **Review this page**. Confirm the finding names a real region, the popup crop shows that region outlined, and the preview's outline sits on it.
3. In the preview: Tab to the Before / After control, switch with the arrow keys, confirm the focus ring and that only the outlined text changes color. Confirm DevTools shows no blocked style sheet (the hash must match) and no network request.
4. Seed a value in a text field, scan, and confirm the field is a flat gray block in the preview and the value appears in neither stored file.
5. Error paths: `chrome://extensions`, a PDF, the extension store, switching tabs mid-scan, scrolling mid-scan, the host not installed, the host installed for a different ID.
6. Speed: measure 30 cold opens and 30 cold scans on the reference Mac. Report p95 from toolbar click to a painted, enabled scan button (target 250 ms) and from Scan to a painted local finding (target 1 second). Record hardware, source pin and failure count.

## Known gaps

- The popup and preview still need independent live review and a 9.5 per screen release score.
- No model review, no redesign builder, and no after view for layout findings. The first finding comes from three local checks only.
- The reference Mac walkthrough observed the recolor in After. A pixel-level check of the recolor remains open.
- No keyboard activation is performed on a live page, so the interaction part of the capture format is validated but never produced.
- The 8 reported regions are chosen by the collector: first heading, main button, up to three hardest-to-read lines, first status, then reading order. That choice has not been checked against human labels.
- Host setup covers Chrome on macOS and Linux. The unpacked extension has no icon and no fixed ID, so the ID must be passed once.
- Font family is the first family in the computed stack, which may differ from the face actually drawn.
