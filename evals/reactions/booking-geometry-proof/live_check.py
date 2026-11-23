"""Exercise each captured client draft independently in an isolated browser."""
import asyncio
from contextlib import ExitStack
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import struct
import sys

sys.path.insert(0, str(Path.cwd() / "evals/v1"))
from render import (Client, StdioTransport, child, dynamic_port, fixture_server,
                    query_json, result_text, wait_ready)

VIEWPORTS = ((1440, 900), (390, 844), (320, 700))
DAYS = ['Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


async def verify(playwriter, env, pages, endpoint, out):
    transport = StdioTransport(command=playwriter, args=[], env=env, cwd=str(out))
    async with Client(transport, timeout=35) as client:
        opened = await client.call_tool("session_new", {"direct": endpoint})
        assert not opened.is_error and " created" in result_text(opened)
        session = result_text(opened).split()[1]

        async def execute(code):
            response = await client.call_tool("execute", {"session": session, "code": code, "timeout":15000})
            output = result_text(response)
            assert not response.is_error, output
            return output

        async def collect(phase, path):
            receipt = await execute("""
                const page = state.page;
                const result = await page.evaluate(() => {
                  const heading = document.querySelector('h1');
                  const group = [...document.querySelectorAll('input[type="radio"]')];
                  const active = document.activeElement;
                  const selected = group.find(input => input.checked);
                  const controls = group.map(input => {
                    const label = input.labels?.[0] || input;
                    const rect = label.getBoundingClientRect();
                    return {value:input.value, label:label.textContent.trim(), w:rect.width, h:rect.height};
                  });
                  const styles = heading ? getComputedStyle(heading) : null;
                  const summary = document.querySelector('#summary-day');
                  const summaryBounds = summary?.getBoundingClientRect();
                  return {title: document.title, text: document.body.innerText, controls,
                    selected: selected?.value || null, active: active?.value || null,
                    visibleFocus: Boolean(active?.matches(':focus-visible')),
                    summary: summary?.textContent || null,
                    scrollY, summaryTop: summaryBounds?.top, summaryBottom: summaryBounds?.bottom,
                    summaryInView: Boolean(summaryBounds && summaryBounds.top >= 0 && summaryBounds.bottom <= innerHeight),
                    font:styles?.fontFamily, size:styles?.fontSize, color:styles?.color,
                    loadedFonts:[...document.fonts].filter(f => f.status==='loaded').map(f=>f.family),
                    width:innerWidth, clientWidth:document.documentElement.clientWidth, scrollWidth:document.documentElement.scrollWidth,
                    reducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches};
                });
                await page.screenshot({path: """ + json.dumps(str(path)) + """, animations:'disabled'});
                console.log('BOOKING ' + JSON.stringify({...result, errors:state.errors}));
            """)
            marker = next(line.split("BOOKING ", 1)[1] for line in receipt.splitlines() if "BOOKING " in line)
            facts = json.loads(marker)
            assert not facts["errors"], facts["errors"]
            data = path.read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            dimensions = struct.unpack(">II", data[16:24])
            assert dimensions == (width, height)
            facts.update(phase=phase, screenshot=path.name, pixel_dimensions=dimensions, sha256=sha256(data).hexdigest())
            return facts

        allowed = json.dumps([entry["url"] for entry in pages.values()])
        await execute(f"""
          await context.route('**/*', route => {{
            const request=route.request();
            const origin=new URL(request.url()).origin;
            const font=(origin==='https://fonts.googleapis.com' && request.resourceType()==='stylesheet') ||
                       (origin==='https://fonts.gstatic.com' && request.resourceType()==='font');
            return request.method()==='GET' && ({allowed}.includes(request.url()) || font)
              ? route.continue() : route.abort();
          }});
        """)
        for arm, entry in pages.items():
            entry["screens"] = []
            for width, height in VIEWPORTS:
                url = json.dumps(entry["url"])
                await execute(f"""
                  state.page=await context.newPage();
                  state.errors=[];
                  state.page.on('pageerror', error => state.errors.push(String(error)));
                  await state.page.setViewportSize({{width:{width},height:{height}}});
                  await state.page.emulateMedia({{reducedMotion:'reduce'}});
                  await state.page.goto({url},{{waitUntil:'load',timeout:12000}});
                  await state.page.evaluate(() => document.fonts.ready.then(() => true));
                """)
                before = await collect("before", out / f"{arm}-{width}-before.png")
                await execute("""
                  const page=state.page;
                  const activeRadio=()=>page.evaluate(()=>document.activeElement?.matches('input[type="radio"]'));
                  for(let i=0;i<12 && !(await activeRadio());i++) await page.keyboard.press('Tab');
                  if(!(await activeRadio())) throw new Error('Booking days are not keyboard reachable');
                  for(let i=0;i<5 && await page.evaluate(()=>document.activeElement.value!=='Friday');i++)
                    await page.keyboard.press('ArrowRight');
                """)
                chosen = await collect("keyboard-friday", out / f"{arm}-{width}-friday.png")
                await execute("""
                  const radio=state.page.locator('input[type="radio"][value="Tuesday"]');
                  const id=await radio.getAttribute('id');
                  if(id) await state.page.locator('label[for='+JSON.stringify(id)+']').click();
                  else await radio.click();
                """)
                alternate = await collect("pointer-tuesday", out / f"{arm}-{width}-tuesday.png")
                shots = [before, chosen, alternate]
                if not alternate["summaryInView"]:
                    await execute("""
                      await state.page.keyboard.press('PageDown');
                      await state.page.waitForFunction(() => {
                        const bounds = document.querySelector('#summary-day')?.getBoundingClientRect();
                        return bounds && bounds.top >= 0 && bounds.bottom <= innerHeight;
                      }, undefined, {timeout: 1800}).catch(() => null);
                    """)
                    shots.append(await collect("scroll-to-summary", out / f"{arm}-{width}-summary.png"))
                await execute("await state.page.close()")
                checks = {
                    "facts": all(all(fact in row["text"].lower() for fact in ("second spin", "41 elm street", "48 hours", "$85", "tune-up")) for row in shots),
                    "days": all([control["value"] for control in row["controls"]] == DAYS for row in shots),
                    "fits_width": all(row["scrollWidth"] <= row["clientWidth"] + 1 for row in shots),
                    "reduced_motion_preference": all(row["reducedMotion"] for row in shots),
                    "keyboard_booking": chosen["selected"] == chosen["active"] == "Friday" and chosen["visibleFocus"] and "Friday" in (chosen["summary"] or ""),
                    "pointer_booking": alternate["selected"] == "Tuesday" and "Tuesday" in (alternate["summary"] or ""),
                    "summary_visible": shots[-1]["summaryInView"],
                }
                entry["screens"].append({"width":width, "checks":checks, "evidence":shots})
    return pages


def main(trial, chrome, playwriter, out):
    out.mkdir()
    home = out / "home"
    home.mkdir()
    profile = out / "isolated-profile"
    env = {key:value for key,value in os.environ.items() if not key.startswith("PLAYWRITER_")}
    port = dynamic_port()
    env.update(HOME=str(home), PLAYWRITER_PORT=str(port), PLAYWRITER_LOG_FILE_PATH=str(out / "playwriter.log"))
    with ExitStack() as stack:
        chrome_args = [chrome, "--headless", "--disable-extensions", "--disable-sync",
                       "--disable-background-networking", "--no-first-run", "--no-default-browser-check",
                       f"--user-data-dir={profile}", "--remote-debugging-address=127.0.0.1",
                       "--remote-debugging-port=0", "about:blank"]
        browser = stack.enter_context(child(chrome_args, out / "chrome.log"))
        cdp = wait_ready(browser, lambda: int((profile / "DevToolsActivePort").read_text().splitlines()[0]))
        version = wait_ready(browser, lambda: query_json(f"http://127.0.0.1:{cdp}/json/version"))
        relay = stack.enter_context(child([playwriter, "serve", "--host", "127.0.0.1"], out / "relay.log", env=env))

        def relay_ready():
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True

        wait_ready(relay, relay_ready)
        pages = {}
        for arm in ("initial","calmer"):
            source = trial / arm / "index.html"
            server = stack.enter_context(fixture_server())
            server.fixture = source.read_bytes()
            digest = sha256(server.fixture).hexdigest()
            call = json.loads((source.parent / "receipt.json").read_text())
            assert call["status"] == "passed" and call["html_sha256"] == digest
            pages[arm] = {"url":f"http://127.0.0.1:{server.server_port}/index.html","html_sha256":digest}
        result = asyncio.run(verify(playwriter, env, pages, version["webSocketDebuggerUrl"], out))
    visible_delta = {}
    for first, second in zip(result["initial"]["screens"], result["calmer"]["screens"], strict=True):
        assert first["width"] == second["width"]
        visible_delta[first["width"]] = {
            a["phase"]: a["sha256"] != b["sha256"]
            for a, b in zip(first["evidence"][:3], second["evidence"][:3], strict=True)
        }
    receipt = {"browser":version["Browser"], "pages":result, "visible_delta":visible_delta}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n")
    screens = [screen for page in result.values() for screen in page["screens"]]
    failures = [{"arm":arm, "width":screen["width"], "failed":[name for name, passed in screen["checks"].items() if not passed]}
                for arm, page in result.items() for screen in page["screens"] if not all(screen["checks"].values())]
    unchanged = [width for width, changes in visible_delta.items() if not all(changes.values())]
    print(json.dumps({"widths":[1440,390,320],"captures":sum(len(screen["evidence"]) for screen in screens),
                      "browser":version["Browser"],"failures":failures,"unchanged":unchanged}))
    raise SystemExit(bool(failures or unchanged))


if __name__ == '__main__':
    main(Path(sys.argv[1]),sys.argv[2],sys.argv[3],Path(sys.argv[4]))
