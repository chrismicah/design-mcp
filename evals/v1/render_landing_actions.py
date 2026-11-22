"""Verify the matched ceramics pages through the shopper's keyboard flow."""

import json

from render import execute, main, sha256


async def interact(client, cell, width):
    path = cell / f"{width}-after.png"
    response = await execute(client, f"""
      const page = state.page;
      const add = page.getByRole('button', {{ name: 'Add to bag', exact: true }});
      const view = page.getByRole('button', {{ name: 'View bag', exact: true }});
      const confirmation = page.getByRole('status');
      const dialog = page.getByRole('dialog', {{ name: 'Your bag' }});
      const before = (await confirmation.textContent({{ timeout: 2000 }})).trim();
      let reached = false;
      for (let tab = 0; tab < 20; tab++) {{
        await page.keyboard.press('Tab');
        if (await add.evaluate(el => el === document.activeElement)) {{
          reached = true;
          break;
        }}
      }}
      if (!reached) throw new Error('Add to bag is outside the keyboard order');
      await page.keyboard.press('Enter');
      const after = (await confirmation.textContent({{ timeout: 2000 }})).trim();
      const count = await page.getByRole('button', {{ name: 'Bag, 1 item', exact: true }}).isVisible();
      const activated = await view.evaluate(el => el === document.activeElement);
      await page.keyboard.press('Enter');
      const opened = await dialog.isVisible();
      const contents = opened ? await dialog.innerText() : '';
      await page.screenshot({{ path: {json.dumps(str(path))}, animations: 'disabled' }});
      await page.keyboard.press('Escape');
      const restored = await view.evaluate(el => el === document.activeElement);
      const closed = !(await dialog.isVisible());
      const passed = reached && activated && before !== after && /added.*bag/i.test(after) &&
        count && opened && contents.includes('Oat Glaze Bowl') && contents.includes('$46') &&
        closed && restored && state.pageErrors.length === 0;
      console.log('LANDING_RESULT ' + JSON.stringify({{ reached, activated, before, after, count,
        opened, contents, closed, restored, passed, pageErrors: state.pageErrors }}));
    """)
    line = next((line for line in response.splitlines() if "LANDING_RESULT " in line), None)
    if not line or not path.is_file():
        raise RuntimeError(f"Missing observed action for {cell.name} at {width}: {response[-600:]}")
    result, _ = json.JSONDecoder().raw_decode(line.split("LANDING_RESULT ", 1)[1])
    result["after_sha256"] = sha256(path.read_bytes())
    return result


if __name__ == "__main__":
    main(interact)
