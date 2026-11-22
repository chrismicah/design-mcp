"""Verify the frozen first-item and return-to-empty flows."""

import json

from render import execute, main, sha256
from render_settings_preview_actions import KEYBOARD


TRAIL = r"""
const save = page.getByRole('button', {name:'Save trail', exact:true});
const remove = page.getByRole('button', {name:'Remove trail', exact:true});
const saved = page.getByRole('region', {name:/^(Your list|Saved trail list)$/i});
const status = page.getByRole('status');
const route = page.getByRole('heading', {name:'Cedar Bend', exact:true});
const startsEmpty = await save.isVisible() && !(await saved.isVisible()) && await route.count() === 1;
await tabTo(save);
await page.keyboard.press('Enter');
const addedToList = await saved.getByRole('heading', {name:'Cedar Bend', exact:true}).isVisible() &&
  await saved.getByText('2.4 miles', {exact:true}).isVisible() && await remove.isVisible() &&
  !(await save.isVisible()) && /added|1 saved trail/i.test(await status.innerText());
await capture(__POPULATED__);
await tabTo(remove);
await page.keyboard.press('Enter');
const restoredEmpty = !(await saved.isVisible()) && await save.isVisible() &&
  await route.count() === 1 && /removed|no trails saved/i.test(await status.innerText());
const focusRestored = await focused(save) || await focused(route);
await capture(__EMPTY__);
const checks = {startsEmpty, addedToList, restoredEmpty, focusRestored};
"""

DRAFT = r"""
const title = page.getByRole('textbox', {name:/^(Article|Draft) title$/i});
const create = page.getByRole('button', {name:'Create draft', exact:true});
const clear = page.getByRole('button', {name:'Clear draft', exact:true});
const status = page.getByRole('status');
const titleText = 'The first edition';
const draft = page.getByRole('heading', {name:titleText, exact:true});
const key = __STORAGE_KEY__;
const stored = () => page.evaluate(name => localStorage.getItem(name), key);
const startsEmpty = await title.isVisible() && !(await clear.isVisible()) && await stored() === null;
await tabTo(create);
await page.keyboard.press('Enter');
const blankRejected = await focused(title) && await title.getAttribute('aria-invalid') === 'true' && await stored() === null;
await page.keyboard.insertText(titleText);
await tabTo(create);
await page.keyboard.press('Enter');
const titleSaved = await draft.isVisible() && await focused(draft) && await stored() === titleText &&
  /draft created/i.test(await status.innerText());
await capture(__POPULATED__);
await page.reload({waitUntil:'domcontentloaded'});
const reopenedDraft = await draft.isVisible() && await stored() === titleText;
await tabTo(clear);
await page.keyboard.press('Enter');
const cleared = await title.isVisible() && await focused(title) && !(await draft.isVisible()) &&
  await stored() === null && /draft cleared/i.test(await status.innerText());
await page.reload({waitUntil:'domcontentloaded'});
const reopenedEmpty = await title.isVisible() && !(await draft.isVisible()) && await stored() === null;
await capture(__EMPTY__);
const checks = {startsEmpty, blankRejected, titleSaved, reopenedDraft, cleared, reopenedEmpty};
"""

REPORT = r"""
const staysLocal = page.url() === url && restricted.length === 0;
console.log('EMPTY_ACTIONS '+JSON.stringify({checks, staysLocal, restricted, pageErrors:state.pageErrors,
  passed:Object.values(checks).every(Boolean) && staysLocal && !state.pageErrors.length}));
"""


async def interact(client, cell, width):
    populated = cell / f"{width}-populated.png"
    empty = cell / f"{width}-empty.png"
    action = {"empty-saved": TRAIL, "empty-drafts": DRAFT}[cell.parent.name]
    allow_reload = "request.method() === 'GET' && request.resourceType() === 'document' && request.url() === url"
    keyboard = KEYBOARD.replace("if (request.method()", f"if ({allow_reload}) return;\n  if (request.method()")
    key = {"none": "editorial-desk.article-draft.v1", "v2": "publishing-desk.demo-draft"}[cell.name]
    script = (keyboard + action + REPORT).replace("__POPULATED__", json.dumps(str(populated)))
    script = script.replace("__EMPTY__", json.dumps(str(empty))).replace("__STORAGE_KEY__", json.dumps(key))
    response = await execute(client, script)
    marker = "EMPTY_ACTIONS "
    line = next((line for line in response.splitlines() if marker in line), None)
    if line is None:
        raise RuntimeError(f"No empty-state receipt for {cell} at {width}: {response[-900:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    for state, path in (("populated", populated), ("empty", empty)):
        outcome[f"{state}_sha256"] = sha256(path.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact, clear_storage_on_navigation=False)
