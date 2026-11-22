"""Replay the exact coffee and train pilot pages through the same keyboard tasks."""

import json
import os
from pathlib import Path

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
const axeContrast = () => page.evaluate(async () => {
  const result = await window.axe.run({runOnly: ['color-contrast']});
  const details = rows => rows.flatMap(row => row.nodes.map(node => ({
    target: node.target, text: node.failureSummary,
    related: [...node.any, ...node.all, ...node.none].flatMap(check =>
      check.data ? [check.data] : [])
  })));
  return {violations: details(result.violations), incomplete: details(result.incomplete),
    passedNodes: result.passes.reduce((total, row) => total + row.nodes.length, 0)};
});
const contrast = {};
async function inspectUnresolved(scan, statePath, backgroundPath) {
  if (!scan.incomplete.length) return;
  const selectors = scan.incomplete.map(row => row.target[0]);
  const elements = await page.evaluate(values => values.map(selector => {
    const node = document.querySelector(selector);
    const {left, top, right, bottom} = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    const svg = node instanceof SVGElement;
    return {selector, box: [left,top,right,bottom], color: svg ? style.fill : style.color, svg};
  }), selectors);
  await page.screenshot({path: statePath, animations: 'disabled'});
  const rule = await page.addStyleTag({content: selectors.join(',') + '{opacity:0!important}'});
  try {
    await page.screenshot({path: backgroundPath, animations: 'disabled'});
  } finally {
    await rule.evaluate(el => el.remove());
  }
  scan.sample = {elements, statePath, backgroundPath};
}
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
  contrast.after = await axeContrast();
  await inspectUnresolved(contrast.after, __PATH__, __AFTER_BG__);
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
  contrast.after = await axeContrast();
  await inspectUnresolved(contrast.after, __PATH__, __AFTER_BG__);
  await page.keyboard.press('Enter');
  restored = !(await ticket.isVisible()) && await isFocused(control);
}
const passed = nextDepartureVisible && startsHidden && reached && revealed && restored;
const outcome = {start, nextDepartureVisible, startsHidden, reached, revealed, restored, passed};
"""


async def interact(client, cell, width):
    path = cell / f"{width}-action.png"
    task = {"landing": _COFFEE, "mobile": _TRAIN}[cell.parent.name]
    axe_path = json.dumps(os.environ["PILOT_AXE_SCRIPT"])
    def capture_path(label):
        return json.dumps(str(cell / f"{width}-{label}.png"))

    setup = (f"await page.addScriptTag({{path:{axe_path}}});\n"
             "contrast.initial = await axeContrast();\n"
             f"await inspectUnresolved(contrast.initial,{capture_path('initial-unresolved')},"
             f"{capture_path('initial-background')});\n")
    exercise = task.replace("__PATH__", json.dumps(str(path))).replace("__AFTER_BG__",
                                                                       capture_path("after-background"))
    result = await execute(client, _COMMON + setup + exercise + """
const local = page.url() === originalUrl && requests.length === 0;
console.log('PILOT_ACTION ' + JSON.stringify({...outcome, viewport: initial, local,
  contrast, pageErrors: state.pageErrors, passed: outcome.passed && local && state.pageErrors.length === 0}));
""")
    line = next((line for line in result.splitlines() if "PILOT_ACTION " in line), None)
    if line is None:
        raise RuntimeError(f"Missing pilot action receipt for {cell} at {width}: {result[-700:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split("PILOT_ACTION ", 1)[1])
    for score in outcome["contrast"].values():
        if "sample" not in score:
            continue
        for key in ("statePath", "backgroundPath"):
            image = Path(score["sample"].pop(key))
            score["sample"][key] = {"file": image.name, "sha256": sha256(image.read_bytes())}
    outcome["action_sha256"] = sha256(path.read_bytes()) if path.is_file() else None
    return outcome


if __name__ == "__main__":
    main(interact)
