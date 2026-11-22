"""Capture both dashboard rounds and measure the keyboard path and type hierarchy."""

import json

import render


PROBE = r"""
const page = state.page;
const focusButton = page.getByRole('button', {name: /^Focus (load )?LS-057$/});
const restoreButton = page.getByRole('button', {name: /^(Exit focus|Show all 5 loads)$/});

async function goTo(button, fallbackKey) {
  for (let i = 0; i < 12; i++) {
    if (await button.evaluate(node => node === document.activeElement)) return;
    await page.keyboard.press(fallbackKey);
  }
  throw new Error('The keyboard could not reach the expected control');
}

const visible = node => node.checkVisibility({visibilityProperty:true, opacityProperty:true});
const measure = () => {
  const id = document.querySelector('#exception-title, #priority-load');
  const delay = document.querySelector('.delay-value, .priority-meta strong');
  const nextIsVisible = [...document.querySelectorAll('th, p, span')].some(
    node => node.textContent.trim() === 'LS-061' && visible(node)
  );
  return {
    viewport: innerWidth, layoutWidth: document.documentElement.scrollWidth,
    rows: [...document.querySelectorAll('tbody tr')].filter(visible).map(tr => tr.innerText),
    idPx: parseFloat(getComputedStyle(id).fontSize),
    delayPx: parseFloat(getComputedStyle(delay).fontSize),
    idColor: getComputedStyle(id).color, delayColor: getComputedStyle(delay).color,
    fonts: [...document.fonts].filter(face => face.status === 'loaded').map(face => face.family),
    focus: document.activeElement?.innerText?.trim(),
    deadlineVisible: nextIsVisible
  };
};
const position = async button => {
  const bounds = await button.boundingBox();
  return {x: Math.round(bounds.x), y: Math.round(bounds.y)};
};

await page.evaluate(() => document.fonts.ready);
const before = await page.evaluate(measure);
const originalPosition = await position(focusButton);
await goTo(focusButton, 'Tab');
await page.keyboard.press('Enter');
const focused = await page.evaluate(measure);
const reversePosition = await position(restoreButton);
await page.screenshot({path: __AFTER__, animations:'disabled'});
const reversePath = await restoreButton.getAttribute('id') === 'focus-action' ? 'Shift+Tab' : 'Tab';
await goTo(restoreButton, reversePath);
await page.keyboard.press('Space');
const restored = await page.evaluate(measure);
const returnedToFocusButton = await focusButton.evaluate(node => node === document.activeElement);
if (before.rows.length !== 5 || focused.rows.length !== 1 || !focused.rows[0].includes('LS-057') ||
    !focused.rows[0].includes('Bay 4') || !focused.rows[0].includes('19') || restored.rows.length !== 5 ||
    !returnedToFocusButton) throw new Error('Unexpected focus or restore outcome');
if ([before, focused, restored].some(state => state.layoutWidth > state.viewport))
  throw new Error('Horizontal overflow at a tested state');
console.log('REACTION_RESULT ' + JSON.stringify({before,focused,restored,originalPosition,reversePosition,
  reversePath,returnedToFocusButton}));
"""


capture_initial = render.capture


async def capture_reaction(client, cell, width, height, url):
    result = await capture_initial(client, cell, width, height, url)
    await render.execute(client, f"""
      state.page = await context.newPage();
      await state.page.setViewportSize({{width:{width}, height:{height}}});
      await state.page.emulateMedia({{reducedMotion:'reduce'}});
      await state.page.goto({json.dumps(url)}, {{waitUntil:'load', timeout:12000}});
    """)
    try:
        after = cell / f"{width}-after.png"
        output = await render.execute(client, PROBE.replace("__AFTER__", json.dumps(str(after))))
        line = next((s.split("REACTION_RESULT ", 1)[1] for s in output.splitlines() if "REACTION_RESULT " in s), None)
        if not line or not after.is_file():
            raise RuntimeError(f"No dashboard keyboard observation: {output[-1200:]}")
        metrics, _ = json.JSONDecoder().raw_decode(line)
        result.update(keyboard=metrics, after_sha256=render.sha256(after.read_bytes()))
        return result
    finally:
        await render.execute(client, "await state.page.close();")


if __name__ == "__main__":
    render.capture = capture_reaction
    render.main()
