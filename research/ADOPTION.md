# Getting users to their first visible improvement

Two products show how to make a browser tool understandable. WAVE runs from the toolbar, displays results on the current page, and processes the page within the browser. VisBug makes spacing and style inspection concrete by letting users point at the page they already have open. Their flows are better activation references than an install walkthrough that starts in an IDE. [WAVE extension](https://wave.webaim.org/extension/) · [VisBug](https://github.com/GoogleChromeLabs/ProjectVisBug)

Responsively opens one site at several viewport sizes. Its observable value is an immediate comparison. The public GitHub API returned 25,575 stars for Responsively and 5,765 for VisBug on November 21, 2026. These are repository interest counts. The proposed experiments measure whether similar affordances help Design MCP users finish and share useful work. [Responsively API](https://api.github.com/repos/responsively-org/responsively-app) · [VisBug API](https://api.github.com/repos/GoogleChromeLabs/ProjectVisBug)

| Experiment | First user action | Metric and next decision |
| --- | --- | --- |
| One-click review | Open the extension on a page and select **Review this page**. Show the first specific issue and its location. | Observe time from install to the first useful finding, completion rate, and requests for help. Fix the highest drop-off before adding another control. |
| Shareable before and after | Compare the page with one proposed change, then optionally export the comparison. Use original or approved assets. | Measure the rate of voluntary exports after a successful preview and repeat scans the following week. Keep exports local until the user chooses where to share. |
| Real-work examples | Let a visitor try a working form, dashboard, or landing page fixture from the install guide. | Measure whether visitors who finish the fixture reach their first successful real scan. Use product recordings and exact before/after captures for a later launch. |

Collect aggregate event counts only after opt-in. Exclude URLs, page text, and screenshots from telemetry. Compare the same fixtures and onboarding steps before attributing gains to a change. Keep the extension's first feedback fast and the next action legible when connection or model service is unavailable.
