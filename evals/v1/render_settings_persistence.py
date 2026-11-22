"""Distinguish a real saved setting from a visible but false confirmation."""

import json

from render import execute, main, sha256


_ACTION = r"""
const page = state.page;
const booking = page.getByRole('switch', {name: 'Booking reminders', exact: true});
const events = page.getByRole('switch', {name: 'Event announcements', exact: true});
const save = page.getByRole('button', {name: /^Save (settings|preferences)$/i});
const status = page.getByRole('status');
const key = __KEY__;
const url = page.url();
const isFocused = target => target.evaluate(node => node === document.activeElement);
const advanceFocus = async target => {
  for (let i = 0; i < 16 && !(await isFocused(target)); i++) await page.keyboard.press('Tab');
  if (!(await isFocused(target))) throw new Error('Could not reach the settings control with Tab');
};
const readStored = () => page.evaluate(name => JSON.parse(localStorage.getItem(name)), key);
await page.evaluate(name => localStorage.removeItem(name), key);
await page.reload({waitUntil: 'domcontentloaded'});
await booking.waitFor({state:'visible'});
const defaultsPassed = await booking.isChecked() && !(await events.isChecked()) && await readStored() === null;
const sent = [];
page.on('request', request => {
  if (!['font','stylesheet','document'].includes(request.resourceType()) || request.method() !== 'GET') {
    sent.push(request.method() + ' ' + request.url());
  }
});
await advanceFocus(booking);
await page.keyboard.press('Space');
await advanceFocus(events);
await page.keyboard.press('Space');
const dirty = /unsaved changes/i.test(await status.innerText());
await advanceFocus(save);
await page.keyboard.press('Enter');
const savedVisible = /^(settings|preferences) saved\.?$/i.test((await status.innerText()).trim());
await page.screenshot({path: __SAVED__, animations:'disabled'});
const stored = await readStored();
await page.reload({waitUntil: 'domcontentloaded'});
await booking.waitFor({state:'visible'});
const reopened = {booking:await booking.isChecked(), events:await events.isChecked()};
const reopenedStored = await readStored();
await page.screenshot({path: __REOPENED__, animations:'disabled'});
const displayedStored = !reopened.booking && reopened.events;
const recordMatches = stored?.bookingReminders === false && stored?.eventAnnouncements === true;
const reopenedRecordMatches = reopenedStored?.bookingReminders === false &&
  reopenedStored?.eventAnnouncements === true;
const persistenceFailed = dirty && savedVisible && !displayedStored && stored === null && reopenedStored === null;
const staysLocal = page.url() === url && sent.length === 0;
const passed = defaultsPassed && dirty && savedVisible && displayedStored && recordMatches && reopenedRecordMatches &&
  staysLocal && !state.pageErrors.length;
await page.evaluate(name => localStorage.removeItem(name), key);
console.log('SETTINGS_PERSISTENCE '+JSON.stringify({
  defaultsPassed, dirty, savedVisible, stored, reopened, reopenedStored, displayedStored, recordMatches,
  reopenedRecordMatches, persistenceFailed,
  staysLocal, sent, pageErrors: state.pageErrors, passed
}));
"""


async def interact(client, cell, width):
    saved = cell / f"{width}-saved.png"
    reopened = cell / f"{width}-reloaded.png"
    key = "coworking.notification-preferences.v1" if cell.name == "none" else "coworking.notification-settings.v1"
    script = _ACTION.replace("__KEY__", json.dumps(key))
    script = script.replace("__SAVED__", json.dumps(str(saved))).replace("__REOPENED__", json.dumps(str(reopened)))
    output = await execute(client, script)
    prefix = "SETTINGS_PERSISTENCE "
    line = next((value for value in output.splitlines() if prefix in value), None)
    if line is None:
        raise RuntimeError(f"No persistence check for {cell} at {width}: {output[-900:]}")
    result, _ = json.JSONDecoder().raw_decode(line.split(prefix, 1)[1])
    result["saved_sha256"] = sha256(saved.read_bytes())
    result["reloaded_sha256"] = sha256(reopened.read_bytes())
    return result


if __name__ == "__main__":
    main(interact, clear_storage_on_navigation=False)
