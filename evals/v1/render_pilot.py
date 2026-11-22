"""Stage, exercise, and verify the three frozen Slice E pilot briefs in Playwriter."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageFilter

from render import execute, main as render, sha256


CASES = ("landing", "dashboard", "mobile")
SOURCE_ROOTS = {
    "N": Path("evidence/baseline/N"),
    "L": Path("evidence/baseline/L"),
    "C": Path("evidence/rebuild/comparison/C"),
    "D": Path("evidence/rebuild/comparison/D"),
}
ACTION = {
    "landing": "Add (one bag|Alto Carmo)",
    "dashboard": "Focus (delay|LS-057)",
    "mobile": "(Reveal|Show) ticket",
}


def source_hashes():
    manifest = Path("evidence/rebuild/comparison/source-results.json")
    return json.loads(manifest.read_text())["results"]


def stage(cells):
    results = source_hashes()
    for arm, root in SOURCE_ROOTS.items():
        for case in CASES:
            source = (root / f"{case}.html").read_bytes()
            if sha256(source) != results[arm][case]["source_sha256"]:
                raise ValueError(f"The frozen source changed in {case}/{arm}")
            target = cells / case / arm
            target.mkdir(parents=True, exist_ok=False)
            (target / "index.html").write_bytes(source)


async def interact(client, cell, width):
    case, arm = cell.parent.name, cell.name
    after = cell / f"{width}-after.png"
    response = await execute(client, f"""
      const page = state.page;
      const caseId = {json.dumps(case)};
      const arm = {json.dumps(arm)};
      const action = page.getByRole('button', {{name: new RegExp({json.dumps(ACTION[case])}, 'i')}});
      const read = async () => page.evaluate((caseId) => {{
        const visible = element => !!element && element.getClientRects().length > 0;
        const text = selector => document.querySelector(selector)?.textContent.trim() ?? '';
        const rows = [...document.querySelectorAll('tbody tr')].filter(visible);
        return {{
          focus: document.activeElement?.textContent.trim().slice(0, 150) ?? '',
          rows: rows.map(row => row.textContent.trim().slice(0, 150)),
          announcement: text('[role="status"], output, #heading'),
          bag: text('#bag, #count, .count'),
          bagContents: text('dialog[open] #contents'),
          ticketVisible: caseId === 'mobile' &&
            [...document.querySelectorAll('b,p')].some(el => visible(el) && el.textContent.trim() === 'TKT-0837')
        }};
      }}, caseId);
      const before = await read();
      let reachable = false;
      for (let n = 0; n < 20; n++) {{
        await page.keyboard.press('Tab');
        if (await action.count() === 1 && await action.evaluate(el => document.activeElement === el)) {{
          reachable = true;
          break;
        }}
      }}
      if (reachable) await page.keyboard.press('Enter');
      const after = await read();
      await page.screenshot({{path: {json.dumps(str(after))}, animations: 'disabled'}});
      let taskResult = false;
      if (caseId === 'landing') {{
        const added = /Alto Carmo.*1|1.*Alto Carmo|1 bag added/i;
        taskResult = !added.test(before.announcement + before.bagContents) &&
          added.test(after.announcement + after.bagContents);
      }} else if (caseId === 'dashboard') {{
        taskResult = before.rows.length === 5 && (
          (arm === 'N' && after.focus.includes('LS-057') && before.focus !== after.focus) ||
          (arm !== 'N' && after.rows.length === 1 && after.rows[0].includes('LS-057'))
        );
      }} else {{
        taskResult = !before.ticketVisible && after.ticketVisible;
      }}
      console.log('PILOT_ACTION ' + JSON.stringify({{input: 'Tab then Enter', reachable, before, after,
        passed: reachable && taskResult && state.pageErrors.length === 0,
        pageErrors: state.pageErrors}}));
    """)
    line = next((line for line in response.splitlines() if "PILOT_ACTION " in line), None)
    if line is None or not after.is_file():
        raise RuntimeError(f"Playwriter produced no task observation: {response[-1000:]}")
    result, _ = json.JSONDecoder().raw_decode(line.split("PILOT_ACTION ", 1)[1])
    result["after_sha256"] = sha256(after.read_bytes())
    return result


def verify(cells):
    results = source_hashes()
    for case in CASES:
        for arm in SOURCE_ROOTS:
            cell = cells / case / arm
            record = json.loads((cell / "render.json").read_text())
            assert record["input_sha256"] == results[arm][case]["source_sha256"]
            assert record["browser"] == "Chrome/158.0.8127.36" and record["renderer"] == "0.12.0"
            assert set(record["captures"]) == {"390", "1440"}
            for width, capture in record["captures"].items():
                assert capture["status"] == "rendered", capture
                original = cell / f"{width}.png"
                assert capture["sha256"] == sha256(original.read_bytes())
                assert capture["interaction"]["after_sha256"] == sha256((cell / f"{width}-after.png").read_bytes())
                blur = cell / f"{width}-blur.png"
                with Image.open(original) as image:
                    image.convert("L").filter(ImageFilter.GaussianBlur(8)).save(blur)
                capture["blur_sha256"] = sha256(blur.read_bytes())
                print(case, arm, width, capture["interaction"]["passed"], flush=True)
            (cell / "render.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--stage", type=Path)
    actions.add_argument("--verify", type=Path)
    options, _ = parser.parse_known_args()
    if options.stage:
        stage(options.stage)
    elif options.verify:
        verify(options.verify)
    else:
        render(interact)
