"""Replay appointment details on the exact benchmark HTML through Playwriter."""

import json

from render import execute, main, sha256


_ACTION = r"""
const page = state.page;
const control = page.locator('button, summary, [role="button"]').filter({hasText: /^\s*Details\s*$/i});
const instructions = page.getByText(/bring a bag.*side door/i).last();
const address = page.getByText('18 Pine Avenue', {exact: true});
const requests = [];
const initialUrl = page.url();
page.on('request', request => requests.push(request.url()));
await control.waitFor({state: 'visible', timeout: 2000});

const labelContext = await address.evaluate(el => {
  const label = /(?:^|\b)(?:address|location|pickup location)\s*:?\s*$/i;
  for (let node = el, depth = 0; node && depth < 3; node = node.parentElement, depth++) {
    const previous = node.previousElementSibling;
    const labelIds = (node.getAttribute('aria-labelledby') || '').trim().split(/\s+/);
    const named = labelIds.some(id => label.test(document.getElementById(id)?.textContent?.trim() || ''));
    if (label.test(previous?.textContent?.trim() || '') || named ||
      label.test(node.getAttribute('aria-label') || '') ||
      /^(address|location|pickup location)\s*:?\s*18 pine avenue$/i.test(node.innerText.trim())) {
      return true;
    }
  }
  return false;
});
const readsInViewport = async target => {
  if (!(await target.isVisible())) return false;
  const box = await target.boundingBox();
  return box && box.x >= 0 && box.y >= 0 && box.x + box.width <= inner.width && box.y + box.height <= inner.height;
};
const inner = await page.evaluate(() => ({width: innerWidth, height: innerHeight}));
const firstViewport = {
  time: await readsInViewport(page.getByText('11:15', {exact: true})),
  day: await readsInViewport(page.getByText('Friday', {exact: true})),
  address: await readsInViewport(address),
  details: await readsInViewport(control)
};
const focused = () => control.evaluate(el => el === document.activeElement);
const expanded = () => control.evaluate(el => el.tagName === 'SUMMARY'
  ? el.parentElement.open
  : el.getAttribute('aria-expanded') === 'true');
const startsCollapsed = !(await instructions.isVisible()) && !(await expanded());
for (let step = 0; step < 16 && !(await focused()); step++) await page.keyboard.press('Tab');
const reachedByKeyboard = await focused();
let opens = false, closes = false;
if (reachedByKeyboard) {
  await page.keyboard.press('Enter');
  await instructions.waitFor({state: 'visible', timeout: 2000}).catch(() => {});
  opens = await instructions.isVisible() && await expanded();
  await page.screenshot({path: __PATH__, animations: 'disabled'});
  await page.keyboard.press('Enter');
  await instructions.waitFor({state: 'hidden', timeout: 2000}).catch(() => {});
  closes = !(await instructions.isVisible()) && !(await expanded()) && await focused();
}
const local = page.url() === initialUrl && requests.length === 0;
const passed = startsCollapsed && reachedByKeyboard && opens && closes && local && !state.pageErrors.length &&
  Object.values(firstViewport).every(Boolean);
console.log('COLLECTION_ACTION ' + JSON.stringify({firstViewport, labelContext, startsCollapsed,
  reachedByKeyboard, opens, closes, local, pageErrors: state.pageErrors, passed}));
"""


async def interact(client, cell, width):
    path = cell / f"{width}-details.png"
    result = await execute(client, _ACTION.replace("__PATH__", json.dumps(str(path))))
    marker = "COLLECTION_ACTION "
    line = next((line for line in result.splitlines() if marker in line), None)
    if line is None:
        raise RuntimeError(f"No collection action receipt for {cell} at {width}: {result[-700:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    outcome["details_sha256"] = sha256(path.read_bytes()) if path.is_file() else None
    return outcome


if __name__ == "__main__":
    main(interact)
