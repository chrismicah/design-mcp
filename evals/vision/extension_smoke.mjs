import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { once } from "node:events";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { openSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const [chrome, cli, extension, output] = process.argv.slice(2);
const latencyRuns = Number(process.env.REVIEW_LATENCY_RUNS ?? 0);
assert.ok(Number.isInteger(latencyRuns) && latencyRuns >= 0 && latencyRuns <= 30);
await mkdir(output, { recursive: true });
const fixture = await readFile(new URL("fixtures/shuttle-dispatch.html", import.meta.url));
const host = createServer((request, response) => {
  if (request.url !== "/dispatch") return response.writeHead(204).end();
  response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  response.end(fixture);
});
host.listen(0, "127.0.0.1");
await once(host, "listening");
const fixtureUrl = `http://127.0.0.1:${host.address().port}/dispatch`;
const profile = join(output, "chrome-profile");
const debugLog = openSync(join(output, "browser.log"), "w");
const browser = spawn(chrome, [
  `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check",
  "--disable-background-networking", "--disable-sync", "--disable-component-update",
  `--disable-extensions-except=${extension}`, `--load-extension=${extension}`,
  "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
  "--window-size=1440,940", fixtureUrl,
], { stdio: ["ignore", debugLog, debugLog] });
const proof = {};
let socket;
const key = (...keys) => execFileSync("xdotool", ["key", "--clearmodifiers", ...keys]);
async function until(description, check, milliseconds = 10000, interval = 120) {
  const deadline = Date.now() + milliseconds;
  while (Date.now() < deadline) {
    const value = await check();
    if (value) return value;
    if (browser.exitCode !== null || browser.signalCode !== null) {
      throw new Error(`Chrome exited: ${browser.exitCode ?? browser.signalCode}`);
    }
    await delay(interval);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

try {
  const endpoint = await until("isolated Chrome", async () => {
    try {
      const [port] = (await readFile(join(profile, "DevToolsActivePort"), "utf8")).split("\n");
      const info = await fetch(`http://127.0.0.1:${port}/json/version`).then(reply => reply.json());
      proof.browser = info.Browser;
      return info.webSocketDebuggerUrl;
    } catch {
      return undefined;
    }
  });
  socket = new WebSocket(endpoint);
  await once(socket, "open");
  let messageId = 0;
  const pending = new Map();
  socket.addEventListener("message", event => {
    const message = JSON.parse(event.data);
    pending.get(message.id)?.(message);
  });
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++messageId;
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error(`CDP timeout: ${method}`));
    }, 5000);
    pending.set(id, message => {
      clearTimeout(timer);
      pending.delete(id);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
    });
    socket.send(JSON.stringify({ id, method, params, sessionId }));
  });
  const findTarget = async predicate => (await send("Target.getTargets")).targetInfos.find(predicate);
  const attach = async target => (await send("Target.attachToTarget", {
    targetId: target.targetId, flatten: true,
  })).sessionId;
  const inspect = async (session, expression) => {
    const output = await send("Runtime.evaluate", {
      expression, returnByValue: true, awaitPromise: true,
    }, session);
    if (output.exceptionDetails) {
      throw new Error(output.exceptionDetails.exception?.description || output.exceptionDetails.text);
    }
    return output.result.value;
  };
  const image = async (session, name) => {
    const shot = await send("Page.captureScreenshot", { format: "png" }, session);
    await writeFile(join(output, name), Buffer.from(shot.data, "base64"));
  };

  const fixturePage = await until("dispatch fixture", () => findTarget(target => target.url === fixtureUrl));
  const fixtureSession = await attach(fixturePage);
  proof.field = await until("seeded private field", async () => inspect(fixtureSession, `(() => {
    const field = document.querySelector('#ops-note');
    if (!field || !field.value.startsWith('fixture-redaction-sentinel-')) return null;
    const r = field.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height,viewport:[innerWidth,innerHeight]};
  })()`));
  const windowId = execFileSync("xdotool", ["search", "--onlyvisible", "--name", "Evening shuttle dispatch"],
    { encoding: "utf8" }).trim().split("\n")[0];
  execFileSync("xdotool", ["windowfocus", "--sync", windowId]);
  const findPopup = () => findTarget(item => /^chrome-extension:\/\/[a-p]{32}\/popup\.html$/.test(item.url));
  key("ctrl+shift+y");
  const target = await until("toolbar popup", findPopup);
  const extensionId = new URL(target.url).hostname;
  proof.extensionId = extensionId;
  const popup = await attach(target);
  const observePopup = () => inspect(popup, `(() => {
    if (!document.body?.dataset.state) return null;
    return {
      state: document.body.dataset.state,
      focus: document.activeElement?.id,
      enabled: !document.querySelector('#scan').disabled,
      status: document.querySelector('#status').textContent,
      command: document.querySelector('#command-text').textContent,
      requestCount: performance.getEntriesByType('resource').filter(entry => /^https?:/.test(entry.name)).length,
      previewUrl: document.querySelector('#open').dataset.url || null
    };
  })()`);
  proof.idle = await until("enabled, keyboard-focused Scan action", async () => {
    const state = await observePopup();
    return state?.state === "idle" && state.focus === "scan" && state.enabled ? state : null;
  });
  assert.equal(proof.idle.requestCount, 0);
  await image(popup, "popup-idle.png");
  key("Return");
  proof.missingHost = await until("missing host recovery", async () => {
    const result = await observePopup();
    return result?.state === "problem" && result.focus === "scan" && result.enabled ? result : null;
  });
  assert.equal(proof.missingHost.command, `design-mcp review --install-host ${extensionId}`);
  execFileSync(cli, ["review", "--install-host", extensionId, "--chrome-user-data-dir", profile], { encoding: "utf8" });
  key("Return");
  proof.result = await until("installed native review result", async () => {
    const result = await observePopup();
    if (result?.state === "problem") throw new Error(result.status);
    return result?.state === "result" ? result : null;
  }, 15000);
  assert.equal(proof.result.focus, "open");
  assert.equal(proof.result.requestCount, 0);
  assert.match(proof.result.status, /1 fields or frames blanked out/);
  await image(popup, "popup-result.png");

  key("Return");
  const previewTarget = await until("preview tab after the popup action", () => findTarget(item => item.url === proof.result.previewUrl));
  const preview = await attach(previewTarget);
  const observePreview = () => inspect(preview, `(() => {
    const after = document.querySelector('#view-after');
    if (!after || document.readyState !== 'complete') return null;
    return {
      focus: document.activeElement?.id,
      title: document.title,
      visible: getComputedStyle(document.querySelector('.state-after')).display !== 'none',
      after: after.checked
    };
  })()`);
  await until("loaded Before and After controls", observePreview);
  for (let step = 0; step < 8 && (await observePreview()).focus !== "view-before"; step++) key("Tab");
  assert.equal((await observePreview()).focus, "view-before");
  await image(preview, "preview-before.png");
  key("Right");
  proof.preview = await observePreview();
  assert.equal(proof.preview.after, true);
  assert.equal(proof.preview.visible, true);
  await image(preview, "preview-after.png");
  proof.previewFolder = dirname(fileURLToPath(proof.result.previewUrl));

  if (latencyRuns) {
    const latency = proof.latency = {
      scope: "Fresh popup documents and one-request native host processes in a warm Chrome session",
      expectedTrials: latencyRuns, trials: [],
    };
    const painted = (session, selector, state) => inspect(session, `(() => {
      const node = document.querySelector(${JSON.stringify(selector)});
      const ready = () => document.body?.dataset.state === ${JSON.stringify(state)} &&
        node?.checkVisibility() && !node.disabled && Boolean(node.textContent?.trim());
      if (document.body?.dataset.state === 'problem') throw new Error(document.querySelector('#status').textContent);
      if (!ready()) return false;
      return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(ready()))));
    })()`);
    const p95 = values => values.toSorted((a, b) => a - b)[Math.ceil(values.length * .95) - 1];
    await send("Target.closeTarget", { targetId: previewTarget.targetId });
    await send("Target.activateTarget", { targetId: fixturePage.targetId });
    for (let trial = 0; trial < latencyRuns; trial++) {
      await until("previous popup to close", async () => !(await findPopup()), 5000, 15);
      const activatedEpoch = Date.now();
      const activated = performance.now();
      key("ctrl+shift+y");
      const inputMs = performance.now() - activated;
      const fresh = await until("fresh toolbar popup", findPopup, 5000, 15);
      const targetMs = performance.now() - activated;
      const session = await attach(fresh);
      await until("painted Scan control", () => painted(session, "#scan", "idle"), 5000, 15);
      const openMs = performance.now() - activated;
      const paint = await inspect(session, `({
        navigationEpoch: performance.timeOrigin,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime ?? null
      })`);
      const scanned = performance.now();
      key("Return");
      await until("painted local finding", () => painted(session, "#finding", "result"), 10000, 15);
      const scanMs = performance.now() - scanned;
      assert.equal(await inspect(session, "!document.querySelector('#fix').hidden"), true);
      latency.trials.push({
        openMs: Math.round(openMs), scanMs: Math.round(scanMs),
        inputMs: Math.round(inputMs), targetMs: Math.round(targetMs),
        popupNavigationMs: Math.round(paint.navigationEpoch - activatedEpoch),
        popupFirstContentfulPaintMs: paint.firstContentfulPaint,
      });
      key("Escape");
    }
    latency.p95 = {
      openMs: p95(latency.trials.map(trial => trial.openMs)),
      scanMs: p95(latency.trials.map(trial => trial.scanMs)),
    };
  }
  proof.passed = true;
} finally {
  await writeFile(join(output, "extension-review.json"), JSON.stringify(proof, null, 2) + "\n");
  socket?.close();
  host.close();
  if (browser.exitCode === null) browser.kill();
}
