"""Verify that both gallery treatments let a keyboard user read the material note."""

import json

from render import execute, main, sha256
from render_settings_preview_actions import KEYBOARD


ACTION = r"""
const show = page.getByRole('button', {name:'Show material note', exact:true});
const hide = page.getByRole('button', {name:'Hide material note', exact:true});
const note = page.getByText(/^Pigment on plaster\.?$/);
const startsCollapsed = !(await note.isVisible()) && await show.getAttribute('aria-expanded') === 'false';
await tabTo(show);
await page.keyboard.press('Enter');
const opens = await note.isVisible() && await hide.getAttribute('aria-expanded') === 'true' &&
  await focused(hide);
const linkedNote = await hide.evaluate(control => {
  const node = document.getElementById(control.getAttribute('aria-controls'));
  return /^Pigment on plaster\.?$/.test(node?.textContent.trim());
});
await capture(__EXPANDED__);
await page.keyboard.press('Enter');
const closes = !(await note.isVisible()) && await show.getAttribute('aria-expanded') === 'false' &&
  await focused(show);
const staysLocal = page.url() === url && restricted.length === 0;
console.log('GALLERY_ACTION '+JSON.stringify({startsCollapsed, opens, linkedNote, closes, staysLocal,
  restricted, pageErrors:state.pageErrors,
  passed:startsCollapsed && opens && linkedNote && closes && staysLocal && !state.pageErrors.length}));
"""


async def interact(client, cell, width):
    shot = cell / f"{width}-expanded.png"
    output = await execute(client, KEYBOARD + ACTION.replace("__EXPANDED__", json.dumps(str(shot))))
    prefix = "GALLERY_ACTION "
    line = next((line for line in output.splitlines() if prefix in line), None)
    if line is None:
        raise RuntimeError(f"No gallery action receipt for {cell} at {width}: {output[-900:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(prefix, 1)[1])
    outcome["expanded_sha256"] = sha256(shot.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact)
