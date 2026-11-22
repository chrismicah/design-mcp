"""Replay reading preferences on sealed builds, including a fresh navigation."""

import json

from render import execute, main, sha256


ACTIONS = r"""
const page = state.page;
const url = page.url();
await page.evaluate(() => {localStorage.clear(); sessionStorage.clear();});
await page.reload({waitUntil:'load'});
await page.evaluate(() => document.fonts.ready);
const radio = name => page.getByRole('radio', {name, exact:true});
const standard = radio('Standard');
const large = radio('Large');
const comfortable = radio('Comfortable');
const compact = radio('Compact');
const reset = page.getByRole('button', {name:'Reset to defaults'});
const sample = page.getByText(/Rest dough for/).first();
const focus = locator => locator.evaluate(node => node === document.activeElement);
const tabTo = async locator => {
  for (let step = 0; step < 24 && !(await focus(locator)); step++) {
    await page.keyboard.press('Tab');
  }
  if (!(await focus(locator))) throw new Error('Expected control is missing from the tab order');
};
const settings = async () => ({
  standard:await standard.isChecked(), large:await large.isChecked(),
  comfortable:await comfortable.isChecked(), compact:await compact.isChecked(),
  controlsVisible:await reset.isVisible() && (await page.getByRole('radio').count() === 4),
  sample:await sample.evaluate(node => {
    const style = getComputedStyle(node);
    const size = parseFloat(style.fontSize);
    return {size, leading:parseFloat(style.lineHeight) / size, text:node.innerText.replace(/\s+/g,' ').trim()};
  })
});
const restricted = [];
page.on('request', request => {
  if (request.method() !== 'GET' ||
      (request.url() !== url && !['font','stylesheet'].includes(request.resourceType()))) {
    restricted.push({method:request.method(), url:request.url()});
  }
});
const initial = await settings();
await tabTo(standard);
await page.keyboard.press('ArrowRight');
const resized = await settings();
await tabTo(comfortable);
await page.keyboard.press('ArrowRight');
const changed = await settings();
await page.screenshot({path:__CHANGED__, animations:'disabled'});
const reopen = async () => {
  await page.goto('about:blank');
  await page.goto(url,{waitUntil:'load'});
  await page.evaluate(() => document.fonts.ready);
  return settings();
};
const reopened = await reopen();
await page.screenshot({path:__REOPENED__, animations:'disabled'});
if (reopened.standard) {
  await tabTo(standard);
  await page.keyboard.press('ArrowRight');
}
if (reopened.comfortable) {
  await tabTo(comfortable);
  await page.keyboard.press('ArrowRight');
}
const beforeReset = await settings();
await tabTo(reset);
await page.keyboard.press('Enter');
await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
const restored = await settings();
await page.screenshot({path:__RESTORED__, animations:'disabled'});
const reopenedAfterReset = await reopen();
const matchesDefaults = state => state.standard && state.comfortable && state.controlsVisible &&
  state.sample.size === initial.sample.size && state.sample.leading === initial.sample.leading;
const checks = {
  startsAtDefaults:initial.standard && initial.comfortable && initial.controlsVisible,
  sizeUpdatesIndependently:resized.large && resized.comfortable && resized.sample.size > initial.sample.size,
  spacingUpdatesIndependently:changed.large && changed.compact &&
    changed.sample.size === resized.sample.size && changed.sample.leading < resized.sample.leading,
  sampleTextPreserved:[initial,resized,changed,reopened,beforeReset,restored,reopenedAfterReset]
    .every(state => state.sample.text === 'Rest dough for 20 minutes.'),
  defaultsRestored:beforeReset.large && beforeReset.compact && matchesDefaults(restored),
  staysLocal:page.url() === url && restricted.length === 0
};
const persistsOnReopen = reopened.large && reopened.compact && reopened.controlsVisible &&
  reopened.sample.size === changed.sample.size && reopened.sample.leading === changed.sample.leading;
const resetPersistsOnReopen = matchesDefaults(reopenedAfterReset);
if (__CHECK_STORAGE_FAILURE__) {
  const storageKeys = await page.evaluate(() => Object.keys(localStorage));
  if (storageKeys.length !== 1) throw new Error('Expected one preference record after reset');
  await page.evaluate(key => localStorage.setItem(key,'{'), storageKeys[0]);
  checks.corruptRecordUsesDefaults = matchesDefaults(await reopen());
  await page.addInitScript(() => {
    const deny = () => { throw new DOMException('Storage unavailable in this test','SecurityError'); };
    Object.defineProperty(Storage.prototype, 'getItem', {value:deny, configurable:true});
    Object.defineProperty(Storage.prototype, 'setItem', {value:deny, configurable:true});
  });
  checks.deniedReadUsesDefaults = matchesDefaults(await reopen());
  await tabTo(standard);
  await page.keyboard.press('ArrowRight');
  const unavailableChange = await settings();
  const announcement = await page.getByRole('status').innerText();
  checks.deniedWriteKeepsControlsWorking = unavailableChange.large && unavailableChange.comfortable &&
    unavailableChange.sample.size > initial.sample.size &&
    /large/i.test(announcement) && !/\b(saved|persisted)\b/i.test(announcement);
}
console.log('READING_ACTIONS '+JSON.stringify({checks, persistsOnReopen, resetPersistsOnReopen, states:{
  initial,resized,changed,reopened,beforeReset,restored,reopenedAfterReset
}, restricted, pageErrors:state.pageErrors, passed:Object.values(checks).every(Boolean) && !state.pageErrors.length}));
"""


async def interact(client, cell, width):
    paths = {state: cell / f"{width}-{state}.png" for state in ("changed", "reopened", "restored")}
    script = ACTIONS.replace("__CHECK_STORAGE_FAILURE__", json.dumps(cell.name == "settings-persistence"))
    for state, path in paths.items():
        script = script.replace(f"__{state.upper()}__", json.dumps(str(path)))
    result = await execute(client, script)
    marker = "READING_ACTIONS "
    line = next((entry for entry in result.splitlines() if marker in entry), None)
    if line is None:
        raise RuntimeError(f"No reading settings action receipt for {cell} at {width}: {result[-900:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    return {**outcome, **{f"{state}_sha256": sha256(path.read_bytes()) for state, path in paths.items()}}


if __name__ == "__main__":
    main(interact, clear_storage_on_navigation=False)
