"""Exercise the workshop reservation flow on the exact candidate and control pages."""

import json

from render import execute, main, sha256


async def interact(client, cell, width):
    path = cell / f"{width}-after.png"
    response = await execute(client, """
      const page = state.page;
      const choices = page.locator('input[type=radio][name=session]');
      const guest = page.locator('#guest-name');
      const email = page.locator('#guest-email');
      const submit = page.getByRole('button', {name:'Reserve seats', exact:true});
      const confirmation = page.getByRole('heading', {name:'Reservation confirmed', exact:true});
      const need = {guest:'Jamie Kirk', email:'jamie@example.com', session:'Sunday at 2 pm'};
      const url = page.url();
      const requests = [];
      page.on('request', request => requests.push(request.method()));

      const focused = async node => await node.evaluate(el => el === document.activeElement);
      async function tabTo(node) {
        for (let step = 0; step < 25; step++) {
          if (await focused(node)) return;
          await page.keyboard.press('Tab');
        }
        throw new Error('Could not reach ' + await node.evaluate(el => el.outerHTML.slice(0, 200)));
      }
      const options = await choices.evaluateAll(nodes => nodes.map(node => node.value));
      await tabTo(choices.first());
      if (!await choices.nth(1).isChecked()) await page.keyboard.press('ArrowRight');
      const choseSunday = await choices.nth(1).isChecked();
      await tabTo(guest);
      await page.keyboard.type(need.guest);
      await tabTo(email);
      await page.keyboard.type('jamie');
      await tabTo(submit);
      await page.keyboard.press('Enter');
      const hint = page.locator('#email-error');
      const invalid = await focused(email) && await email.getAttribute('aria-invalid') === 'true' &&
        await hint.isVisible() && /email/i.test(await hint.innerText()) && !await confirmation.isVisible();
      const invalidRetainedInput = await guest.inputValue() === need.guest && await choices.nth(1).isChecked();
      await page.keyboard.press('ControlOrMeta+a');
      await page.keyboard.type(need.email);
      await tabTo(submit);
      await page.keyboard.press('Enter');
      const confirmed = await confirmation.isVisible() && await focused(confirmation);
      const details = confirmed ? {
        session: await page.locator('#confirmed-session, #confirmed-time').innerText(),
        seats: await page.locator('#confirmed-seats').innerText(),
        name: await page.locator('#confirmed-name').innerText(),
        email: await page.locator('#confirmed-email').innerText(),
      } : {};
      const detailsMatch = details.session === need.session && details.name === need.guest &&
        details.email === need.email && ['1','1 seat'].includes(details.seats);
      await page.screenshot({path: SHOT_PATH, animations:'disabled'});
      let edited = false;
      if (confirmed) {
        await tabTo(page.getByRole('button', {name:'Edit reservation', exact:true}));
        await page.keyboard.press('Enter');
        edited = !await confirmation.isVisible() && await guest.isVisible() &&
          await guest.inputValue() === need.guest && await email.inputValue() === need.email &&
          await choices.nth(1).isChecked() &&
          await focused(page.locator('#booking-title, #form-title'));
      }
      const local = page.url() === url && requests.length === 0;
      const passed = options.join('|') === 'Saturday at 10 am|Sunday at 2 pm' &&
        choseSunday && invalid && invalidRetainedInput && confirmed && detailsMatch && edited && local &&
        state.pageErrors.length === 0;
      console.log('VENUE_RESULT '+JSON.stringify({options,choseSunday,invalid,invalidRetainedInput,
        confirmed,details,detailsMatch,edited,local,passed,pageErrors:state.pageErrors}));
    """.replace("SHOT_PATH", json.dumps(str(path))))
    line = next((line for line in response.splitlines() if "VENUE_RESULT " in line), None)
    if line is None or not path.is_file():
        raise RuntimeError(f"Missing reservation outcome for {cell.name} at {width}: {response[-1000:]}")
    outcome, _ = json.JSONDecoder().raw_decode(line.split("VENUE_RESULT ", 1)[1])
    outcome["after_sha256"] = sha256(path.read_bytes())
    return outcome


if __name__ == "__main__":
    main(interact)
