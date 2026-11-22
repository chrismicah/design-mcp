import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { once } from "node:events";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { closeSync, openSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const [chrome, cli, extension, output, fixturePath] = process.argv.slice(2);
const mac = process.platform === "darwin";
const macKeyHelper = process.env.DESIGN_MCP_CHROME_KEY_HELPER;
const latencyRuns = Number(mac ? process.env.REVIEW_LATENCY_RUNS ?? 0 : 0);
assert(Number.isInteger(latencyRuns) && latencyRuns >= 0 && latencyRuns <= 30);
await mkdir(output, { recursive: true });
const fixture = await readFile(fixturePath || new URL("fixtures/shuttle-dispatch.html", import.meta.url));
const host = createServer((request, response) => {
  if (request.url !== "/dispatch") return response.writeHead(204).end();
  response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
  response.end(fixture);
});
const proof = {};
let browser;
let browserError;
let socket;
const runMacKeyHelper = (...args) => execFileSync(macKeyHelper, args, { encoding: "utf8", timeout: 8000 });
const key = name => {
  if (!mac) return execFileSync("xdotool", ["key", "--clearmodifiers", name]);
  assert(browser.pid && browser.exitCode === null && browser.signalCode === null, "Owned Chrome is not running");
  proof.lastKey = name;
  return runMacKeyHelper(String(browser.pid), name);
};
async function until(description, check, milliseconds = 10000, pollMs = 120) {
  const deadline = Date.now() + milliseconds;
  while (Date.now() < deadline) {
    if (browserError) throw browserError;
    const value = await check();
    if (value) return value;
    if (browser.exitCode !== null || browser.signalCode !== null) {
      throw new Error(`Chrome exited: ${browser.exitCode ?? browser.signalCode}`);
    }
    await delay(pollMs);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

try {
  if (mac) {
    proof.passed = false;
    proof.phase = "desktop input preflight";
    assert(macKeyHelper, "Set DESIGN_MCP_CHROME_KEY_HELPER for the macOS keyboard proof");
    proof.inputPreflight = runMacKeyHelper("--preflight").trim();
  }
  host.listen(0, "127.0.0.1");
  await once(host, "listening");
  const fixtureUrl = `http://127.0.0.1:${host.address().port}/dispatch`;
  const profile = mac ? await mkdtemp(join(output, "chrome-profile-")) : join(output, "chrome-profile");
  const debugLog = openSync(join(output, "browser.log"), "w");
  try {
    browser = spawn(chrome, [
      `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check",
      "--disable-background-networking", "--disable-sync", "--disable-component-update",
      `--disable-extensions-except=${extension}`, `--load-extension=${extension}`,
      "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
      "--window-size=1440,940", fixtureUrl,
    ], { stdio: ["ignore", debugLog, debugLog] });
    browser.on("error", error => { browserError = error; });
  } finally {
    closeSync(debugLog);
  }
  if (mac) {
    proof.phase = "browser startup";
    proof.chromePid = browser.pid;
    proof.chromeProfile = profile;
  }
  const endpoint = await until("isolated Chrome", async () => {
    try {
      const [port] = (await readFile(join(profile, "DevToolsActivePort"), "utf8")).split("\n");
      if (!/^\d+$/.test(port)) return undefined;
      const info = await fetch(`http://127.0.0.1:${port}/json/version`).then(reply => reply.json());
      proof.browser = info.Browser;
      const url = new URL(info.webSocketDebuggerUrl);
      if (url.origin === `ws://127.0.0.1:${port}`) return url.href;
    } catch {
      return undefined;
    }
  });
  socket = new WebSocket(endpoint);
  await once(socket, "open", { signal: AbortSignal.timeout(5000) });
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
    const output = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true }, session);
    if (output.exceptionDetails) {
      throw new Error(output.exceptionDetails.exception?.description || output.exceptionDetails.text);
    }
    return output.result.value;
  };
  const image = async (session, name) => {
    const shot = await send("Page.captureScreenshot", { format: "png" }, session);
    await writeFile(join(output, name), Buffer.from(shot.data, "base64"));
  };
  const browserKey = async (session, key, windowsVirtualKeyCode, nativeVirtualKeyCode, text) => {
    const event = {key, code: key, windowsVirtualKeyCode, nativeVirtualKeyCode};
    const down = text ? {type: "keyDown", text} : {type: "rawKeyDown"};
    await send("Input.dispatchKeyEvent", {...event, ...down}, session);
    await send("Input.dispatchKeyEvent", {...event, type: "keyUp"}, session);
  };

  const fixturePage = await until("dispatch fixture", () => findTarget(target => target.url === fixtureUrl));
  const fixtureSession = await attach(fixturePage);
  proof.field = await until("seeded private field", async () => inspect(fixtureSession, `(() => {
    const field = document.querySelector('#ops-note');
    if (!field || !field.value.startsWith('fixture-redaction-sentinel-')) return null;
    const r = field.getBoundingClientRect();
    return {x:r.x,y:r.y,width:r.width,height:r.height,viewport:[innerWidth,innerHeight]};
  })()`));
  const isPopup = item => /^chrome-extension:\/\/[a-p]{32}\/popup\.html$/.test(item.url);
  if (mac) {
    proof.phase = "toolbar shortcut";
    assert.equal(await findTarget(isPopup), undefined, "Popup must start closed");
    key("Command+Shift+Y");
  } else {
    const windowId = execFileSync("xdotool", ["search", "--onlyvisible", "--name", "Evening shuttle dispatch"],
      { encoding: "utf8" }).trim().split("\n")[0];
    execFileSync("xdotool", ["windowfocus", "--sync", windowId]);
    key("ctrl+shift+y");
  }
  const target = await until("toolbar popup", () => findTarget(isPopup));
  const extensionId = new URL(target.url).hostname;
  proof.extensionId = extensionId;
  const popup = await attach(target);
  const observePopup = () => inspect(popup, `(() => {
    if (location.href !== ${JSON.stringify(target.url)} || document.readyState !== 'complete') return null;
    const scan = document.querySelector('#scan');
    const status = document.querySelector('#status');
    const command = document.querySelector('#command-text');
    const result = document.querySelector('#result');
    const finding = document.querySelector('#finding');
    const open = document.querySelector('#open');
    const missing = Object.entries({
      'body[data-state]': document.body?.dataset.state, '#scan': scan, '#status': status,
      '#command-text': command, '#result': result, '#finding': finding, '#open': open,
    }).filter(([, node]) => !node).map(([selector]) => selector);
    if (missing.length) {
      throw new Error('The loaded toolbar popup is missing: ' + missing.join(', '));
    }
    return {
      state: document.body.dataset.state,
      focus: document.activeElement?.id,
      enabled: !scan.disabled,
      status: status.textContent,
      command: command.textContent,
      finding: result.hidden ? null : finding.textContent,
      requestCount: performance.getEntriesByType('resource').filter(entry => /^https?:/.test(entry.name)).length,
      previewUrl: open.dataset.url || null
    };
  })()`);
  proof.idle = await until("enabled, keyboard-focused Scan action", async () => {
    const state = await observePopup();
    return state?.state === "idle" && state.focus === "scan" && state.enabled ? state : null;
  });
  assert.equal(proof.idle.requestCount, 0);
  await image(popup, "popup-idle.png");
  if (mac) {
    proof.phase = "missing native host";
    proof.popupActionDriver = "cdp-key";
    await browserKey(popup, "Enter", 13, 36, "\r");
  } else {
    key("Return");
  }
  proof.missingHost = await until("missing host recovery", async () => {
    const result = await observePopup();
    return result?.state === "problem" && result.focus === "scan" && result.enabled ? result : null;
  });
  assert.equal(proof.missingHost.command, `design-mcp review --install-host ${extensionId}`);
  if (mac) {
    assert.match(proof.missingHost.status, /One step left: connect the local reviewer/);
    await image(popup, "popup-missing-host.png");
    proof.phase = "profile-scoped native host install and retry";
  }
  execFileSync(cli, ["review", "--install-host", extensionId, "--chrome-user-data-dir", profile], { encoding: "utf8" });
  if (mac) {
    proof.nativeHostManifest = join(profile, "NativeMessagingHosts", "com.design_mcp.review.json");
    const manifest = JSON.parse(await readFile(proof.nativeHostManifest, "utf8"));
    proof.nativeHostLauncher = manifest.path;
    assert.deepEqual(manifest.allowed_origins, [`chrome-extension://${extensionId}/`]);
    assert.equal(manifest.path, join(dirname(proof.nativeHostManifest), "design-mcp-review-host"));
    await inspect(popup, `(() => {
      const events = [];
      window.__reviewSmokeInput = events;
      for (const type of ['keydown', 'click']) {
        document.addEventListener(type, event => {
          if (events.length < 12) {
            events.push({type, key:event.key, target:event.target.id, trusted:event.isTrusted});
          }
        }, {capture:true});
      }
      return true;
    })()`);
  }
  if (mac) {
    assert.equal((await observePopup()).focus, "scan");
    await browserKey(popup, "Enter", 13, 36, "\r");
    proof.hostRetryInput = await inspect(popup, "window.__reviewSmokeInput");
    assert(proof.hostRetryInput.some(event => event.type === "click" && event.target === "scan" && event.trusted),
      "Chrome did not deliver a trusted click to the focused Scan control");
  } else {
    key("Return");
  }
  proof.result = await until("installed native review result", async () => {
    const result = await observePopup();
    if (mac) proof.retryPopup = result;
    if (result?.state === "problem") throw new Error(result.status);
    return result?.state === "result" ? result : null;
  }, 15000);
  assert.equal(proof.result.focus, "open");
  assert.equal(proof.result.requestCount, 0);
  assert.match(proof.result.status, /1 fields or frames blanked out/);
  if (mac) {
    assert.match(proof.result.finding, /^“Boarding begins at 6:30 p\.m\.” is hard to read at \d+ px wide: its text color #9d958d on #f6f2eb measures 2\.6 to 1, and text this size needs at least 4\.5 to 1\.$/);
  }
  await image(popup, "popup-result.png");

  const findPreview = () => findTarget(item => item.url === proof.result.previewUrl);
  let previewTarget;
  if (mac) {
    proof.phase = "open saved preview and switch by keyboard";
    assert.equal((await observePopup()).focus, "open");
    assert.equal(await findPreview(), undefined, "The saved preview must start closed");
    // Opening a tab can close the toolbar popup before Chrome acknowledges Enter.
    const [input, observed] = await Promise.allSettled([
      browserKey(popup, "Enter", 13, 36, "\r"),
      until("new saved preview tab", findPreview),
    ]);
    proof.previewOpenInput = input.status === "fulfilled" ? "acknowledged" : String(input.reason);
    if (observed.status === "rejected") throw observed.reason;
    previewTarget = observed.value;
  } else {
    key("Return");
    previewTarget = await until("preview tab after the popup action", findPreview);
  }
  const preview = await attach(previewTarget);
  const observePreview = (session = preview) => inspect(session, `(() => {
    const after = document.querySelector('#view-after');
    if (!after || document.readyState !== 'complete') return null;
    return {
      focus: document.activeElement?.id,
      title: document.title,
      finding: document.querySelector('h1').textContent,
      before: document.querySelector('#view-before').checked,
      visible: getComputedStyle(document.querySelector('.state-after')).display !== 'none',
      afterImageVisible: getComputedStyle(document.querySelector('.shot .after')).display !== 'none',
      after: after.checked
    };
  })()`);
  const initial = await until("loaded Before and After controls", observePreview);
  if (mac) {
    assert.equal(initial.before, true);
    assert.equal(initial.visible, false);
    assert.equal(initial.afterImageVisible, false);
    assert.equal(initial.finding, proof.result.finding);
  }
  for (let step = 0; step < 8 && (await observePreview()).focus !== "view-before"; step++) {
    if (mac) await browserKey(preview, "Tab", 9, 48);
    else key("Tab");
  }
  assert.equal((await observePreview()).focus, "view-before");
  await image(preview, "preview-before.png");
  if (mac) {
    proof.previewKeyDriver = "cdp-key";
    await browserKey(preview, "ArrowRight", 39, 124);
  } else {
    key("Right");
  }
  proof.preview = await until("keyboard-selected After", async () => {
    const state = await observePreview();
    proof.lastPreviewState = state;
    if (!state?.after || !state.visible) return null;
    return !mac || (state.focus === "view-after" && state.afterImageVisible) ? state : null;
  });
  assert.equal(proof.preview.after, true);
  assert.equal(proof.preview.visible, true);
  await image(preview, "preview-after.png");
  proof.previewFolder = dirname(fileURLToPath(proof.result.previewUrl));
  if (mac) {
    assert.equal(proof.preview.focus, "view-after");
    assert.equal(proof.preview.afterImageVisible, true);
    proof.phase = "reopen saved preview";
    assert((await send("Target.closeTarget", { targetId: previewTarget.targetId })).success);
    const reopened = await send("Target.createTarget", { url: proof.result.previewUrl });
    assert.notEqual(reopened.targetId, previewTarget.targetId);
    const newTarget = await until("reopened file tab", () => findTarget(item =>
      item.targetId === reopened.targetId && item.url === proof.result.previewUrl));
    const session = await attach(newTarget);
    proof.reopened = await until("reopened local preview", () => observePreview(session));
    assert.equal(proof.reopened.title, initial.title);
    assert.equal(proof.reopened.finding, initial.finding);
    assert.equal(proof.reopened.before, true);
    assert.equal(proof.reopened.visible, false);
    assert.equal(proof.reopened.afterImageVisible, false);
    await image(session, "preview-reopened.png");
    if (latencyRuns) {
      proof.phase = "measure hosted popup and local finding";
      proof.latency = {
        scope: "Fresh popup documents and one-request native hosts in a warm hosted Chrome session",
        drivers: {open: "macOS shortcut", scan: "CDP keyboard"},
        expectedTrials: latencyRuns,
        trials: [],
      };
      const findPopup = () => findTarget(isPopup);
      const painted = (sessionId, selector, state) => inspect(sessionId, `(() => {
        const ready = () => {
          const node = document.querySelector(${JSON.stringify(selector)});
          return document.readyState === 'complete' &&
            document.body?.dataset.state === ${JSON.stringify(state)} &&
            node?.checkVisibility() && !node.disabled && Boolean(node.textContent.trim());
        };
        if (document.body?.dataset.state === 'problem') throw new Error(document.querySelector('#status').textContent);
        if (!ready()) return false;
        return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(ready()))));
      })()`);
      assert((await send("Target.closeTarget", {targetId: newTarget.targetId})).success);
      await send("Target.activateTarget", {targetId: fixturePage.targetId});
      for (let trial = 0; trial < latencyRuns; trial++) {
        await until("previous popup closed", async () => !(await findPopup()), 5000, 15);
        const openedAt = performance.now();
        key("Command+Shift+Y");
        const opened = await until("fresh toolbar popup", findPopup, 5000, 15);
        const tab = await attach(opened);
        await until("painted enabled Scan", () => painted(tab, "#scan", "idle"), 5000, 15);
        const openMs = performance.now() - openedAt;
        assert.equal(await inspect(tab, "document.activeElement?.id"), "scan");
        const scannedAt = performance.now();
        await browserKey(tab, "Enter", 13, 36, "\r");
        await until("painted finding", () => painted(tab, "#finding", "result"), 10000, 15);
        const scanMs = performance.now() - scannedAt;
        assert.match(await inspect(tab, "document.querySelector('#finding').textContent"), /2\.6 to 1/);
        proof.latency.trials.push({number: trial + 1, openMs, scanMs});
        assert((await send("Target.closeTarget", {targetId: opened.targetId})).success);
      }
      const p95 = metric => proof.latency.trials.map(row => row[metric]).toSorted((a, b) => a - b)[
        Math.ceil(latencyRuns * .95) - 1];
      proof.latency.p95 = {openMs: p95("openMs"), scanMs: p95("scanMs")};
    }
    proof.phase = "browser checks complete";
    proof.browserChecksPassed = true;
  } else {
    proof.passed = true;
  }
} catch (error) {
  proof.passed = false;
  proof.error = error.stack || String(error);
  throw error;
} finally {
  socket?.close();
  host.close();
  if (browser?.exitCode === null) browser.kill();
  await writeFile(join(output, "extension-review.json"), JSON.stringify(proof, null, 2) + "\n");
}
