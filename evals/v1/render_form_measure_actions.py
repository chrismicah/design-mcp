"""Replay the two exact candidate and control forms with keyboard input."""

import json

from render import execute, main, sha256


_ACTION = r"""
const page = state.page;
const exhibit = __EXHIBIT__;
const form = page.locator('main form');
const first = form.getByLabel(exhibit ? /^Contact name$/i : /^Order number$/i);
const email = form.getByLabel(/^Email(?: address)?$/i);
const size = form.getByRole('spinbutton', {name: /^Group size$/i});
const submit = form.locator('button[type=submit]');
const radios = form.getByRole('radio');
const choice = radios.filter({visible: true}).nth(1);
const edit = page.getByRole('button', {name: /^Edit (request|details)$/i});
const confirmation = page.locator('#confirmation-title');

const firstValue = exhibit ? 'River Perez' : 'RS-1842';
const emailValue = 'visitor@example.com';
const expectedValue = exhibit ? 'Guided visit' : 'Wrong item';
const confirmedSize = '25 people';
const destination = page.url();
const requests = [];
const valueOf = target => target.inputValue();
const hasFocus = target => target.evaluate(el => document.activeElement === el);
const tabTo = async target => {
  for (let steps = 0; steps < 20; steps++) {
    if (await hasFocus(target)) return true;
    await page.keyboard.press('Tab');
  }
  return false;
};
const typeAt = async (target, value) => {
  if (!(await tabTo(target))) throw new Error('Could not reach a required form field with Tab');
  await page.keyboard.press('Meta+a');
  await page.keyboard.insertText(value);
};
const activate = async target => {
  if (!(await tabTo(target))) throw new Error('Could not reach a required form action with Tab');
  await page.keyboard.press('Enter');
};
const invalidEvidence = target => target.evaluate(el => {
  const ids = (el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean);
  const specific = ids.map(id => document.getElementById(id)).filter(node => node && !node.hidden)
    .map(node => node.textContent.trim()).filter(Boolean);
  return {
    accessibleError: el.getAttribute('aria-invalid') === 'true' && specific.some(Boolean),
    nativeError: !el.validity.valid && Boolean(el.validationMessage),
    errorText: specific.join(' ') || el.validationMessage
  };
});
const staysLocal = request => {
  const origin = new URL(request.url).origin;
  return request.method === 'GET' && (
    (origin === 'https://fonts.googleapis.com' && request.type === 'stylesheet') ||
    (origin === 'https://fonts.gstatic.com' && request.type === 'font')
  );
};

await first.waitFor({state:'visible'});
page.on('request', request => requests.push({
  url: request.url(), type: request.resourceType(), method: request.method()
}));
await activate(submit);
const missing = await invalidEvidence(first);
const missingRejected = await hasFocus(first) && !(await confirmation.isVisible()) &&
  (missing.accessibleError || missing.nativeError);

await typeAt(first, firstValue);
await typeAt(email, 'invalid');
if (exhibit) await typeAt(size, '26');
const radioIndex = async () => radios.evaluateAll(items => items.findIndex(item => item === document.activeElement));
for (let steps = 0; steps < 20 && (await radioIndex()) < 0; steps++) await page.keyboard.press('Tab');
if ((await radioIndex()) < 0) throw new Error('Could not enter the radio group with Tab');
const key = await radioIndex() === 0 ? 'ArrowRight' : 'Space';
await page.keyboard.press(key);
const choiceSelected = await choice.isChecked();
await activate(submit);
const emailError = await invalidEvidence(email);
const emailRejected = await hasFocus(email) && !(await confirmation.isVisible()) &&
  (emailError.accessibleError || emailError.nativeError);
const retainedOnError = await valueOf(first) === firstValue && await choice.isChecked();
await typeAt(email, emailValue);

let rangeRejected = true;
let rangeMessage = null;
if (exhibit) {
  await activate(submit);
  rangeMessage = await invalidEvidence(size);
  rangeRejected = await hasFocus(size) && !(await confirmation.isVisible()) &&
    (rangeMessage.accessibleError || rangeMessage.nativeError);
  await typeAt(size, '25');
}
await activate(submit);
const confirmed = await confirmation.isVisible() && await hasFocus(confirmation);
const summary = confirmed ? await confirmation.evaluate(el => el.closest('section').innerText) : '';
const correctSummary = summary.includes(expectedValue) && (!exhibit || summary.includes(confirmedSize));
await page.screenshot({path: __PATH__, animations:'disabled'});
let retainedOnEdit = false;
if (confirmed) {
  await activate(edit);
  retainedOnEdit = await hasFocus(first) && !(await confirmation.isVisible()) &&
    await valueOf(first) === firstValue && await valueOf(email) === emailValue && await choice.isChecked() &&
    (!exhibit || await valueOf(size) === '25');
}
const local = page.url() === destination && requests.every(staysLocal);
const passed = missingRejected && choiceSelected && emailRejected && retainedOnError && rangeRejected &&
  confirmed && correctSummary && retainedOnEdit && local && !state.pageErrors.length;
console.log('FORM_MEASURE_ACTION '+JSON.stringify({missingRejected, choiceSelected, emailRejected, retainedOnError,
  rangeRejected, confirmed, correctSummary, retainedOnEdit, local, passed, missing, emailError,
  rangeMessage, actionRequests: requests, pageErrors:state.pageErrors}));
"""


async def interact(client, cell, width):
    path = cell / f"{width}-confirmed.png"
    script = _ACTION.replace("__EXHIBIT__", json.dumps(cell.parent.name == "form-exhibition"))
    response = await execute(client, script.replace("__PATH__", json.dumps(str(path))))
    marker = "FORM_MEASURE_ACTION "
    line = next((line for line in response.splitlines() if marker in line), None)
    if line is None or not path.is_file():
        raise RuntimeError(f"Missing form action receipt for {cell} at {width}: {response[-800:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split(marker, 1)[1])
    outcome["confirmed_sha256"] = sha256(path.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact)
