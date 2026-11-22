"""Replay the exact coffee and train pilot pages through the same keyboard tasks."""

import json

from render import execute, main, sha256


_COMMON = r"""
const page = state.page;
const isFocused = target => target.evaluate(el => el === document.activeElement);
const tabTo = async target => {
  for (let step = 0; step < 16; step++) {
    if (await isFocused(target)) return true;
    await page.keyboard.press('Tab');
  }
  return false;
};
const pixels = target => target.evaluate(el => {
  const box = el.getBoundingClientRect();
  return {left: box.left, top: box.top, right: box.right, bottom: box.bottom};
});
const initial = await page.evaluate(() => ({width: innerWidth, height: innerHeight}));
const originalUrl = page.url();
const requests = [];
page.on('request', request => requests.push(request.url()));
"""

_COFFEE = r"""
const buy = page.locator('#add-to-bag');
const roastDate = page.getByText('November 19', {exact: true});
const bag = page.getByRole('dialog', {name: 'Your bag'});
const openBag = page.locator('#open-bag');
const count = page.locator('#bag-count');
const start = {button: await pixels(buy), roastDate: await pixels(roastDate)};
const factsVisible = await roastDate.isVisible();
const reached = await tabTo(buy);
let correctBag = false, restored = false, openedOnAdd = false;
if (reached) {
  await page.keyboard.press('Enter');
  const added = (await count.textContent()).trim() === '1';
  openedOnAdd = await bag.isVisible();
  if (!openedOnAdd && added && await tabTo(openBag)) await page.keyboard.press('Enter');
  await bag.waitFor({state: 'visible', timeout: 2000}).catch(() => {});
  const copy = await bag.isVisible() ? await bag.innerText() : '';
  correctBag = added && copy.includes('Alto Carmo') && copy.includes('$19');
  await page.screenshot({path: __PATH__, animations: 'disabled'});
  await page.keyboard.press('Escape');
  await bag.waitFor({state: 'hidden', timeout: 2000}).catch(() => {});
  restored = !(await bag.isVisible()) && await isFocused(openedOnAdd ? buy : openBag);
}
const passed = factsVisible && reached && correctBag && restored;
const outcome = {start, factsVisible, reached, correctBag, restored, openedOnAdd, passed};
"""

_TRAIN = r"""
const toggle = page.locator('button, summary').filter({hasText: 'Show ticket'});
await toggle.waitFor({state: 'visible', timeout: 2000});
const control = await toggle.elementHandle();
const ticket = page.getByText('TKT-0837', {exact: true});
const later = page.locator('button time[datetime="08:58"]');
const first = page.locator('time[datetime="08:42"]').first();
const start = {
  later: await pixels(later),
  departure: await pixels(first),
  toggle: await pixels(control)
};
const nextDepartureVisible = await later.isVisible() &&
  start.later.top >= 0 && start.later.bottom <= initial.height;
const startsHidden = !(await ticket.isVisible());
const reached = await tabTo(control);
let revealed = false, restored = false;
if (reached) {
  await page.keyboard.press('Enter');
  revealed = await ticket.isVisible();
  await page.screenshot({path: __PATH__, animations: 'disabled'});
  await page.keyboard.press('Enter');
  restored = !(await ticket.isVisible()) && await isFocused(control);
}
const passed = nextDepartureVisible && startsHidden && reached && revealed && restored;
const outcome = {start, nextDepartureVisible, startsHidden, reached, revealed, restored, passed};
"""


async def interact(client, cell, width):
    path = cell / f"{width}-action.png"
    task = {"landing": _COFFEE, "mobile": _TRAIN}[cell.parent.name]
    result = await execute(client, _COMMON + task.replace("__PATH__", json.dumps(str(path))) + """
const local = page.url() === originalUrl && requests.length === 0;
console.log('PILOT_ACTION ' + JSON.stringify({...outcome, viewport: initial, local,
  pageErrors: state.pageErrors, passed: outcome.passed && local && state.pageErrors.length === 0}));
""")
    line = next((line for line in result.splitlines() if "PILOT_ACTION " in line), None)
    if line is None:
        raise RuntimeError(f"Missing pilot action receipt for {cell} at {width}: {result[-700:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split("PILOT_ACTION ", 1)[1])
    outcome["action_sha256"] = sha256(path.read_bytes()) if path.is_file() else None
    return outcome


if __name__ == "__main__":
    main(interact)
