"""Verify an invalid, valid and editable maintenance request using the keyboard."""

import json

from render import execute, main, sha256


async def interact(client, cell, width):
    path = cell / f"{width}-after.png"
    response = await execute(client, f"""
      const page = state.page;
      const building = page.getByRole('textbox', {{name: 'Building', exact: true}});
      const location = page.getByRole('textbox', {{name: 'Location', exact: true}});
      const description = page.getByRole('textbox', {{name: 'Description', exact: true}});
      const submit = page.getByRole('button', {{name: 'Prepare request', exact: true}});
      const prepared = page.getByRole('heading', {{name: 'Request prepared locally', exact: true}});
      const safety = page.getByRole('radio', {{name: 'Safety issue', exact: true}});
      const edit = page.getByRole('button', {{name: 'Edit details', exact: true}});
      const destination = page.url();
      const values = ['Ferry House', 'West stairwell', 'Light has gone out'];

      const isFocused = async target => await target.count() === 1 &&
        await target.evaluate(el => el === document.activeElement);
      const tabTo = async target => {{
        for (let n = 0; n < 20; n++) {{
          if (await isFocused(target)) return true;
          await page.keyboard.press('Tab');
        }}
        return false;
      }};
      const geometry = await building.evaluate(el => {{
        const box = el.getBoundingClientRect();
        const style = getComputedStyle(el, '::placeholder');
        const input = getComputedStyle(el);
        const context2d = document.createElement('canvas').getContext('2d');
        context2d.font = [style.fontStyle, style.fontWeight, style.fontSize, style.fontFamily].join(' ');
        const letters = Math.max(0, [...el.placeholder].length - 1);
        const letterSpacing = parseFloat(style.letterSpacing) || 0;
        return {{
          placeholder: el.placeholder, top: box.top,
          requiredPx: context2d.measureText(el.placeholder).width + letterSpacing * letters,
          availablePx: el.clientWidth - parseFloat(input.paddingInlineStart) - parseFloat(input.paddingInlineEnd)
        }};
      }});
      geometry.fits = geometry.availablePx >= geometry.requiredPx;
      const requests = [];
      page.on('request', req => requests.push({{method: req.method(), url: req.url()}}));

      if (!await tabTo(submit)) throw new Error('Cannot reach Prepare request by keyboard');
      await page.keyboard.press('Enter');
      const invalid = await building.getAttribute('aria-invalid') === 'true' &&
        await isFocused(building) && !(await prepared.isVisible());

      const fields = [building, location, description];
      for (const [index, field] of fields.entries()) {{
        if (!await tabTo(field)) throw new Error('Could not reach text field by keyboard');
        await page.keyboard.type(values[index]);
      }}
      const urgency = page.locator('input[type=radio][name=urgency]:focus');
      if (!await tabTo(urgency)) throw new Error('Could not reach urgency by keyboard');
      if (!await isFocused(safety)) await page.keyboard.press('ArrowRight');
      if (!await safety.isChecked()) await page.keyboard.press('Space');
      const urgencySelected = await safety.isChecked();

      if (!await tabTo(submit)) throw new Error('Cannot reach Prepare request after entry');
      await page.keyboard.press('Enter');
      const confirmation = await prepared.isVisible() && await isFocused(prepared);
      const contents = confirmation ? await prepared.evaluate(el => el.closest('section').innerText) : '';
      const expectedDetails = [...values, 'Safety issue'].every(value => contents.includes(value));
      await page.screenshot({{path:{json.dumps(str(path))}, animations:'disabled'}});
      let editing = false;
      if (await tabTo(edit)) {{
        await page.keyboard.press('Enter');
        const currentValues = await Promise.all(fields.map(field => field.inputValue()));
        editing = await isFocused(building) && !(await prepared.isVisible()) &&
          currentValues.every((value, index) => value === values[index]) && await safety.isChecked();
      }}
      const local = page.url() === destination && requests.length === 0;
      const passed = invalid && urgencySelected && confirmation && expectedDetails && editing && local &&
        state.pageErrors.length === 0;
      console.log('MAINTENANCE_RESULT '+JSON.stringify({{invalid, urgencySelected, confirmation,
        expectedDetails, editing, local, passed, geometry, contents, pageErrors:state.pageErrors}}));
    """)
    line = next((line for line in response.splitlines() if "MAINTENANCE_RESULT " in line), None)
    if line is None or not path.is_file():
        raise RuntimeError(f"Missing maintenance outcome for {cell.name} at {width}: {response[-1000:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split("MAINTENANCE_RESULT ", 1)[1])
    outcome["after_sha256"] = sha256(path.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact)
