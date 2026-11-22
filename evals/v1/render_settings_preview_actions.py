"""Exercise the frozen display-settings and supplier digest flows by keyboard."""

import json

from render import execute, main, sha256


KEYBOARD = r"""
const page = state.page;
const url = page.url();
const focused = control => control.evaluate(node => node === document.activeElement);
const tabTo = async control => {
  for (let step = 0; step < 24 && !(await focused(control)); step++) {
    await page.keyboard.press('Tab');
  }
  if (!(await focused(control))) throw new Error('Expected control is missing from the tab order');
};
const restricted = [];
page.on('request', request => {
  if (request.method() !== 'GET' || !['font','stylesheet'].includes(request.resourceType())) {
    restricted.push({method:request.method(), url:request.url()});
  }
});
const capture = path => page.screenshot({path, animations:'disabled'});
"""

DISPLAY = r"""
const dateFirst = page.getByRole('radio', {name:/^Month first/});
const dayFirst = page.getByRole('radio', {name:/^Day first/});
const fahrenheit = page.getByRole('radio', {name:'Fahrenheit', exact:true});
const celsius = page.getByRole('radio', {name:'Celsius', exact:true});
const preview = page.getByRole('region', {name:'Live preview', exact:true});
const reset = page.getByRole('button', {name:'Reset to defaults', exact:true});
const status = page.getByRole('status');
const shows = (date, temperature) => Promise.all([
  preview.getByText(date, {exact:true}).isVisible(),
  preview.getByText(temperature, {exact:true}).isVisible()
]).then(results => results.every(Boolean));
const startsAtDefaults = await dateFirst.isChecked() && await fahrenheit.isChecked() &&
  await shows('November 21, 2026', '68°F');
await tabTo(dateFirst);
await page.keyboard.press('ArrowRight');
const dateUpdatesIndependently = await dayFirst.isChecked() && await shows('21 November 2026', '68°F');
await tabTo(fahrenheit);
await page.keyboard.press('ArrowRight');
const temperatureUpdates = await celsius.isChecked() && await shows('21 November 2026', '20°C');
await capture(__CHANGED__);
await tabTo(reset);
await page.keyboard.press('Enter');
const defaultsRestored = await dateFirst.isChecked() && await fahrenheit.isChecked() &&
  await shows('November 21, 2026', '68°F') && /defaults restored/i.test(await status.innerText());
await capture(__RESTORED__);
const checks = {startsAtDefaults, dateUpdatesIndependently, temperatureUpdates, defaultsRestored};
"""

DIGEST = r"""
const frequency = name => page.getByRole('radio', {name, exact:true});
const weekly = frequency('Weekly');
const daily = frequency('Daily');
const off = frequency('Off');
const day = page.getByRole('combobox', {name:'Delivery day'})
  .or(page.getByRole('radiogroup', {name:'Delivery day'}));
const save = page.getByRole('button', {name:'Save preferences', exact:true});
const summary = page.locator('#saved-schedule');
const startsWeekly = await weekly.isChecked() && await day.isVisible() &&
  (await summary.innerText()).trim() === 'Weekly on Monday';
await tabTo(weekly);
await page.keyboard.press('ArrowLeft');
const dailyHidesDay = await daily.isChecked() && !(await day.isVisible());
await page.keyboard.press('Tab');
const hiddenDayOutOfTabOrder = await focused(save);
await tabTo(save);
await page.keyboard.press('Enter');
const dailySaved = (await summary.innerText()).trim() === 'Daily';
await capture(__CHANGED__);
await tabTo(daily);
await page.keyboard.press('ArrowLeft');
const offHidesDay = await off.isChecked() && !(await day.isVisible());
await tabTo(save);
await page.keyboard.press('Enter');
const offSaved = (await summary.innerText()).trim() === 'Off';
await tabTo(off);
await page.keyboard.press('ArrowLeft');
const weeklyRestoresDay = await weekly.isChecked() && await day.isVisible();
await tabTo(save);
await page.keyboard.press('Enter');
const weeklySaved = (await summary.innerText()).trim() === 'Weekly on Monday';
await capture(__RESTORED__);
const checks = {startsWeekly, dailyHidesDay, hiddenDayOutOfTabOrder, dailySaved,
  offHidesDay, offSaved, weeklyRestoresDay, weeklySaved};
"""

REPORT = r"""
const staysLocal = page.url() === url && restricted.length === 0;
console.log('SETTINGS_ACTIONS '+JSON.stringify({checks, staysLocal, restricted, pageErrors:state.pageErrors,
  passed:Object.values(checks).every(Boolean) && staysLocal && !state.pageErrors.length}));
"""


async def interact(client, cell, width):
    changed = cell / f"{width}-changed.png"
    restored = cell / f"{width}-restored.png"
    action = {"settings-language": DISPLAY, "settings-digest": DIGEST}[cell.parent.name]
    script = KEYBOARD + action + REPORT
    script = script.replace("__CHANGED__", json.dumps(str(changed))).replace("__RESTORED__", json.dumps(str(restored)))
    result = await execute(client, script)
    marker = "SETTINGS_ACTIONS "
    line = next((line for line in result.splitlines() if marker in line), None)
    if line is None:
        raise RuntimeError(f"No settings action receipt for {cell} at {width}: {result[-900:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    for state, path in (("changed", changed), ("restored", restored)):
        outcome[f"{state}_sha256"] = sha256(path.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact)
