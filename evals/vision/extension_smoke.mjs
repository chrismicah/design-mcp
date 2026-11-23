import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawn } from "node:child_process";
import { once } from "node:events";
import { mkdir, readFile, realpath, writeFile } from "node:fs/promises";
import { openSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { setTimeout as delay } from "node:timers/promises";

const [chrome, cli, extension, output, fixturePath, ...flags] = process.argv.slice(2);
const pastedUrlProof = flags.includes("--pasted-url-e2e");
const publicFixtureUrl = "https://designsystem.digital.gov/templates/form-templates/address-form/";
await mkdir(output, { recursive: true });
const fixture = await readFile(fixturePath || new URL("fixtures/shuttle-dispatch.html", import.meta.url));
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
  "--ozone-platform=x11",
  "--disable-background-networking", "--disable-sync", "--disable-component-update",
  `--disable-extensions-except=${extension}`, `--load-extension=${extension}`,
  "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
  "--window-size=1440,940", fixtureUrl,
], { stdio: ["ignore", debugLog, debugLog] });
const proof = {};
let socket;
const key = (...keys) => execFileSync("xdotool", ["key", "--clearmodifiers", ...keys]);
async function until(description, check, milliseconds = 10000) {
  const deadline = Date.now() + milliseconds;
  while (Date.now() < deadline) {
    const value = await check();
    if (value) return value;
    if (browser.exitCode !== null || browser.signalCode !== null) {
      throw new Error(`Chrome exited: ${browser.exitCode ?? browser.signalCode}`);
    }
    await delay(120);
  }
  const reason = `Timed out waiting for ${description}`;
  proof.failureReason = reason;
  throw new Error(reason);
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
    const output = await send("Runtime.evaluate", { expression, returnByValue: true }, session);
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
  const isPopup = item => /^chrome-extension:\/\/[a-p]{32}\/popup\.html$/.test(item.url);
  proof.toolbarActivations = [];
  async function openToolbarPopup(flow) {
    await send("Target.activateTarget", { targetId: fixturePage.targetId });
    // CDP can report the page before the X11 top-level window is visible.
    const windowId = await until("visible dispatch fixture window", () => {
      try {
        const ids = execFileSync("xdotool", ["search", "--onlyvisible", "--all", "--pid",
          String(browser.pid), "--name", "^Evening shuttle dispatch($| - )"],
        { encoding: "utf8" }).trim().split("\n");
        assert.equal(ids.length, 1, "Expected one visible window for the launched fixture");
        return ids[0];
      } catch (error) {
        if (error.status !== 1 || error.signal) throw error;
        return undefined;
      }
    });

    const activation = { flow, windowId, attempts: [], disappearedTargets: [] };
    proof.toolbarActivations.push(activation);
    let lastAttempt = -Infinity;
    let opening;
    return until(`toolbar popup for ${flow}`, async () => {
      const popupTarget = await findTarget(isPopup);
      if (popupTarget) {
        assert.ok(activation.attempts.length, "The journey must open a new popup using the shortcut");
        try {
          if (opening?.targetId !== popupTarget.targetId) {
            opening = { targetId: popupTarget.targetId, session: await attach(popupTarget) };
          }
          const ready = await inspect(opening.session,
            "document.body?.dataset?.state === 'idle' && document.activeElement?.id === 'scan'");
          if (ready) {
            activation.targetId = popupTarget.targetId;
            return { target: popupTarget, session: opening.session };
          }
        } catch (error) {
          if (!/^(Session with given id not found|No target with given id found)\.?$/.test(error.message)) {
            throw error;
          }
          activation.disappearedTargets.push(popupTarget.targetId);
          opening = undefined;
        }
        return null;
      }
      // Give a pending shortcut time to open without a second key toggling it shut.
      if (activation.attempts.length < 2 && performance.now() - lastAttempt >= 6000) {
        execFileSync("xdotool", ["windowactivate", "--sync", windowId], { timeout: 2000 });
        const active = execFileSync("xdotool", ["getactivewindow"], { encoding: "utf8" }).trim();
        assert.equal(active, windowId, "Shortcut would go to a different X11 window");
        const pageFocused = await inspect(fixtureSession, "document.hasFocus()");
        activation.attempts.push({ pageFocused });
        key("ctrl+shift+y");
        lastAttempt = performance.now();
      }
      return null;
    }, 15000);
  }
  const { target, session: popup } = await openToolbarPopup("active tab");
  const extensionId = new URL(target.url).hostname;
  proof.extensionId = extensionId;
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
  const scopedHistory = await realpath(join(profile, "Design MCP", "reviews"));
  assert.equal(dirname(await realpath(proof.previewFolder)), scopedHistory);
  proof.profileHistoryVerified = true;

  if (pastedUrlProof) {
    // Exercise URL validation in the actual toolbar popup before entering the URL flow.
    await until("the active-tab toolbar popup to close", async () => !await findTarget(isPopup));
    const { target: urlPopupTarget, session: urlPopup } = await openToolbarPopup("pasted URL");
    assert.equal(new URL(urlPopupTarget.url).hostname, extensionId);
    assert.notEqual(urlPopupTarget.targetId, target.targetId);
    const urlState = () => inspect(urlPopup, `(() => ({
      state: document.body?.dataset.state,
      focus: document.activeElement?.id,
      hint: document.querySelector('#url-hint')?.textContent,
      resultHidden: document.querySelector('#result')?.hidden
    }))()`);
    await until("URL entry field in toolbar popup", () => inspect(urlPopup, "Boolean(document.querySelector('#url'))"));
    await inspect(urlPopup, "document.querySelector('#url').focus()");
    execFileSync("xdotool", ["type", "--clearmodifiers", "localhost:3000"]);
    key("Return");
    proof.localhostRejected = await until("inline localhost rejection", async () => {
      const value = await urlState();
      return /public web address/i.test(value.hint) && value.resultHidden && value.focus === "url" ? value : null;
    });
    assert.equal(proof.localhostRejected.state, "idle");
    assert.equal(await findTarget(item => item.url.includes("popup.html?view=url")), undefined);
    key("ctrl+a");
    execFileSync("xdotool", ["type", "--clearmodifiers", publicFixtureUrl]);
    const pasteStarted = performance.now();
    key("Return");
    const pastedTarget = await until("new extension review view", () => findTarget(item =>
      /^chrome-extension:\/\/[a-p]{32}\/popup\.html\?view=url$/.test(item.url)), 25000);
    const pastedView = await attach(pastedTarget);
    const pastedState = () => inspect(pastedView, `(() => document.querySelector('#where') ? ({
      state: document.body.dataset.state,
      focus: document.activeElement?.id,
      finding: document.querySelector('#finding').textContent,
      status: document.querySelector('#status').textContent,
      path: document.querySelector('#path').textContent,
      previewUrl: document.querySelector('#open').dataset.url || null,
      previewVisible: !document.querySelector('#where').hidden
    }) : null)()`);
    proof.pastedResult = await until("pasted URL result and inline capture", async () => {
      const value = await pastedState();
      if (value?.state === "problem") throw new Error(value.status);
      return value?.state === "result" && value.previewVisible && value.previewUrl ? value : null;
    }, 30000);
    assert.equal(proof.pastedResult.focus, "open");
    assert.match(proof.pastedResult.path, /preview\.html$/);
    assert.ok(proof.pastedResult.finding);
    proof.pastedSubmitToCaptureMs = Math.round(performance.now() - pasteStarted);
    assert.equal(await findTarget(item => item.url === publicFixtureUrl), undefined);
    await image(pastedView, "pasted-url-result.png");
    key("Return");
    const pastedPreviewTarget = await until("saved pasted result", () => findTarget(item => item.url === proof.pastedResult.previewUrl));
    const pastedPreview = await attach(pastedPreviewTarget);
    const observeSaved = () => inspect(pastedPreview, `(() => {
      const capture = document.querySelector('svg.shot');
      return capture && document.readyState === 'complete' ? {
        title: document.title, label: capture.getAttribute('aria-label'), width: capture.getAttribute('width')
      } : null;
    })()`);
    proof.pastedPreview = await until("saved capture in the preview", observeSaved);
    assert.match(proof.pastedPreview.title, /^Review of /);
    assert.equal(proof.pastedPreview.width, "1440");
    await send("Page.reload", {}, pastedPreview);
    assert.deepEqual(await until("capture after reopening the preview", observeSaved), proof.pastedPreview);
    const pastedPreviewPath = fileURLToPath(proof.pastedResult.previewUrl);
    const savedReviewDir = dirname(await realpath(pastedPreviewPath));
    assert.equal(dirname(savedReviewDir), scopedHistory);
    const savedEvidence = JSON.parse(await readFile(join(savedReviewDir, "evidence.json"), "utf8"));
    assert.equal(savedEvidence.capture.source, "pasted-url");
    assert.equal(savedEvidence.capture.url, publicFixtureUrl);
    const [frame] = savedEvidence.frames;
    assert.equal(frame.viewport.width, 1440);
    assert.ok(frame.masks.applied && frame.masks.counts.field > 0);
    proof.pastedMaskCount = frame.masks.counts.field;
    proof.pastedEvidencePath = join(savedReviewDir, "evidence.json");
    const previewHtml = await readFile(pastedPreviewPath, "utf8");
    const [, captureData] = previewHtml.match(/data:image\/png;base64,([A-Za-z0-9+/=]+)/);
    proof.pastedScreenshotSha256 = createHash("sha256").update(Buffer.from(captureData, "base64")).digest("hex");
    assert.equal(proof.pastedScreenshotSha256, frame.screenshot.sha256);
    await image(pastedPreview, "pasted-url-preview.png");
    proof.pastedUrlE2e = true;
  }
  proof.passed = true;
} finally {
  await writeFile(join(output, "extension-review.json"), JSON.stringify(proof, null, 2) + "\n");
  socket?.close();
  host.close();
  if (browser.exitCode === null) browser.kill();
}
