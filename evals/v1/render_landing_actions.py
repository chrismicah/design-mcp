"""Exercise the radio and bike-booking controls on both frozen builds."""

import json

from render import execute, main, sha256


async def interact(client, cell, width):
    path = cell / f"{width}-after.png"
    receipt = await execute(client, f"""
      const page = state.page;
      const radio = {json.dumps(cell.parent.name == "landing-radio")};
      const target = radio ? page.getByRole('button', {{ name: /^Listen live/ }})
                           : page.getByRole('radio', {{ name: 'Tuesday', exact: true }});
      const summary = page.locator(radio ? '#listener-state, #listener-status' : '#summary-day, #selected-day');
      const before = await summary.textContent({{ timeout: 2000 }});
      let reached = false;
      for (let tab = 0; tab < 20; tab++) {{
        await page.keyboard.press('Tab');
        if (await target.count() === 1 && await target.evaluate(el => document.activeElement === el)) {{
          reached = true;
          break;
        }}
      }}
      let selected = false;
      if (reached && radio) {{
        await page.keyboard.press('Enter');
        selected = await page.getByRole('button', {{ name: 'Stop listening' }}).isVisible();
      }} else if (reached) {{
        for (let day = 0; day < 3; day++) await page.keyboard.press('ArrowRight');
        selected = await page.getByRole('radio', {{ name: 'Friday', exact: true }}).isChecked();
      }}
      const after = await summary.textContent({{ timeout: 2000 }});
      await page.screenshot({{ path: {json.dumps(str(path))}, animations: 'disabled' }});
      let reversible = false;
      if (selected && radio) {{
        await page.keyboard.press('Enter');
        reversible = await page.getByRole('button', {{ name: /^Listen live/ }}).isVisible();
      }} else if (selected) {{
        await page.keyboard.press('ArrowLeft');
        reversible = await page.getByRole('radio', {{ name: 'Thursday', exact: true }}).isChecked() &&
          (await summary.textContent({{ timeout: 2000 }})).trim() === 'Thursday';
      }}
      const changed = before !== after && (radio ? /live/i.test(after) : after.trim() === 'Friday');
      console.log('LANDING_RESULT ' + JSON.stringify({{ reached, selected, before, after, reversible,
        passed: reached && selected && changed && reversible && state.pageErrors.length === 0,
        final: await summary.textContent({{ timeout: 2000 }}), pageErrors: state.pageErrors }}));
    """)
    line = next((line for line in receipt.splitlines() if "LANDING_RESULT " in line), None)
    if not line or not path.is_file():
        raise RuntimeError(f"Missing observed action for {cell.name} at {width}: {receipt[-600:]}")
    result, _ = json.JSONDecoder().raw_decode(line.split("LANDING_RESULT ", 1)[1])
    result["after_sha256"] = sha256(path.read_bytes())
    return result


if __name__ == "__main__":
    main(interact)
