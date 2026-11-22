"""Exercise the exact frozen tool search and volunteer booking pages."""

import json

from render import execute, main, sha256
from render_settings_preview_actions import KEYBOARD


SEARCH = r"""
const query = page.getByRole('searchbox');
const empty = page.getByRole('heading', {name:/No (?:tools match|matches for).*chain saw/i});
const suggest = page.getByRole('button', {name:/search for.*pruning saw/i});
const result = page.getByRole('heading', {name:'Folding Pruning Saw', exact:true});
const visibleCount = page.getByText(/1 result for.*pruning saw/i);
const availability = page.getByText('Available', {exact:true});
const startsEmpty = (await query.inputValue()) === 'chain saw' &&
  (await empty.isVisible()) && (await suggest.isVisible()) && (await result.count()) === 0;
const showsCountBeforeAction = await page.getByText('1 available tool',{exact:true}).isVisible();
await tabTo(suggest);
await page.keyboard.press('Enter');
const findsOneTool = (await query.inputValue()) === 'pruning saw' &&
  (await result.count()) === 1 && (await result.isVisible()) &&
  (await visibleCount.isVisible()) && (await availability.isVisible()) &&
  (await empty.count()) === 0;
const focusOnMatchedTool = await focused(result);
await capture(__CHANGED__);

await tabTo(query);
await page.keyboard.press('ControlOrMeta+a');
await page.keyboard.insertText('chain saw');
await page.keyboard.press('Enter');
const canReturnToEmpty = (await query.inputValue()) === 'chain saw' &&
  (await empty.isVisible()) && (await suggest.isVisible()) && (await result.count()) === 0;
await capture(__SECOND__);
const checks = {startsEmpty,findsOneTool,focusOnMatchedTool,canReturnToEmpty};
const observations = {showsCountBeforeAction};
"""

SHIFTS = r"""
await page.evaluate(() => {localStorage.clear(); sessionStorage.clear();});
await page.reload({waitUntil:'load'});
await page.evaluate(() => document.fonts.ready);
const empty = page.getByText(/No shifts booked/i);
const available = page.getByRole('region', {name:'Available shift', exact:true});
const booking = page.locator('#booking');
const reserve = page.getByRole('button',{name:'Reserve shift',exact:true});
const offer = page.getByRole('heading',{name:'Packing',exact:true});
const date = /Wednesday/i;
const time = /4\s*[–-]\s*6\s*pm/i;
const startsEmpty = (await empty.isVisible()) && !(await booking.isVisible()) &&
  (await offer.count()) === 1 && (await reserve.count()) === 1 && (await reserve.isVisible()) &&
  date.test(await available.innerText()) && time.test(await available.innerText());
const initialGeometry = await reserve.evaluate(element => {
  const rect = element.getBoundingClientRect();
  return {top:rect.top,bottom:rect.bottom,viewport:innerHeight};
});
await tabTo(reserve);
await page.keyboard.press('Enter');
const bookedHere = page.url() === url && (await booking.isVisible()) &&
  (await booking.getByRole('heading',{name:'Packing',exact:true}).isVisible()) &&
  date.test(await booking.innerText()) && time.test(await booking.innerText()) &&
  /booked/i.test(await booking.innerText()) && !(await empty.isVisible()) &&
  (await reserve.count()) === 0;
const focusOnBooking = await booking.evaluate(element => element.contains(document.activeElement));
await capture(__CHANGED__);
await page.goto('about:blank');
await page.goto(url,{waitUntil:'load'});
const bookingRetainedOnFreshNavigation = await booking.isVisible();
await capture(__SECOND__);
const checks = {startsEmpty,bookedHere,focusOnBooking};
const observations = {initialGeometry,bookingRetainedOnFreshNavigation};
"""

REPORT = r"""
const staysLocal = page.url() === url && restricted.length === 0;
console.log('RECOVERY_ACTIONS '+JSON.stringify({checks, observations, staysLocal, restricted,
  pageErrors:state.pageErrors, passed:Object.values(checks).every(Boolean) && staysLocal && !state.pageErrors.length}));
"""


async def interact(client, cell, width):
    paths = {state: cell / f"{width}-{state}.png" for state in ("changed", "second")}
    action = {"empty-search": SEARCH, "empty-shifts": SHIFTS}[cell.parent.name]
    # A same-origin GET is expected during the explicit reopen; other
    # requests still go through the benchmark's loopback and font allowlist.
    allow_document = "if (request.method() === 'GET' && request.url() === url && request.resourceType() === 'document') return;"
    keyboard = KEYBOARD.replace("  if (request.method()", f"  {allow_document}\n  if (request.method()")
    script = keyboard + action + REPORT
    for state, path in paths.items():
        script = script.replace(f"__{state.upper()}__", json.dumps(str(path)))
    result = await execute(client, script)
    marker = "RECOVERY_ACTIONS "
    line = next((entry for entry in result.splitlines() if marker in entry), None)
    if line is None:
        raise RuntimeError(f"No empty recovery receipt for {cell} at {width}: {result[-900:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    return {**outcome, **{f"{state}_sha256": sha256(path.read_bytes()) for state, path in paths.items()}}


if __name__ == "__main__":
    main(interact, clear_storage_on_navigation=False)
