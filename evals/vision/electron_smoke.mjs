import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { app, BrowserWindow, screen } from "electron";
import { exportDesignCapture } from "../../integrations/desktop/electron.mjs";

const [cli, destination] = process.argv.slice(-2);
const fixture = fileURLToPath(new URL("fixtures/electron-review.html", import.meta.url));
const manualInput = process.env.DESIGN_MCP_ELECTRON_MANUAL_INPUT === "1";

await mkdir(destination, { recursive: true });
app.setPath("userData", join(destination, "isolated-user-data"));
const proof = { electron: process.versions.electron, platform: process.platform };
let window;

async function focusWindow() {
  if (process.platform === "darwin") {
    app.focus({ steal: true });
    window.focus();
    window.webContents.focus();
    for (let pending = 0; pending < 30 && !window.isFocused(); pending++) await delay(50);
    assert.equal(window.isFocused(), true);
    proof.input = "focused Electron webContents";
  } else {
    const windowId = execFileSync("xdotool", ["search", "--onlyvisible", "--name", "^Desk review fixture$"],
      { encoding: "utf8" }).trim().split("\n").at(-1);
    execFileSync("xdotool", ["windowfocus", "--sync", windowId]);
    proof.input = "X11 keyboard";
  }
}

function press(keyCode) {
  if (process.platform === "darwin") {
    assert.equal(window.isFocused(), true);
    window.webContents.sendInputEvent({ type: "keyDown", keyCode });
    if (keyCode === "Return") window.webContents.sendInputEvent({ type: "char", keyCode });
    window.webContents.sendInputEvent({ type: "keyUp", keyCode });
  } else {
    execFileSync("xdotool", ["key", "--clearmodifiers", keyCode]);
  }
}

async function capture(name) {
  const evidencePath = join(destination, name + ".json");
  const controls = await exportDesignCapture(window, evidencePath);
  const evidence = await readFile(evidencePath, "utf8");
  assert.equal(JSON.parse(evidence).regions.length, controls);
  assert.doesNotMatch(evidence, /desktop-review-fixture-private-marker/);
  const review = JSON.parse(execFileSync(cli, ["review-app", evidencePath], { encoding: "utf8" }));
  assert.equal(review.controls_reviewed, 4);
  assert.equal(review.platform, "electron");
  assert.deepEqual(review.viewport, [880, 640]);
  const [width, height] = review.viewport;
  const scale = screen.getDisplayMatching(window.getBounds()).scaleFactor;
  const image = await window.webContents.capturePage();
  assert.equal(image.isEmpty(), false);
  // Electron can return either CSS pixels or the display's backing pixels.
  const size = image.getSize();
  assert.ok(
    (size.width === width && size.height === height) ||
      (size.width === Math.round(width * scale) && size.height === Math.round(height * scale)),
    `Unexpected capture size ${size.width} × ${size.height} for ${width} × ${height} at ${scale}×`,
  );
  (proof.screenshot_sizes ??= {})[name] = { ...size, display_scale: scale };
  await writeFile(join(destination, name + ".png"), image.toPNG());
  return { evidencePath, evidence, findings: review.findings.map(({ code, region }) => [code, region]) };
}

app.whenReady().then(async () => {
  try {
    window = new BrowserWindow({
      width: 880, height: 640, useContentSize: true,
      webPreferences: { contextIsolation: true, sandbox: true, nodeIntegration: false },
    });
    window.removeMenu();
    await window.loadFile(fixture);
    assert.equal(window.webContents.getURL(), pathToFileURL(fixture).href);
    await focusWindow();
    const observe = () => window.webContents.executeJavaScript(
      "({ focus: document.activeElement.id, status: document.querySelector('#status').textContent })"
    );

    if (manualInput) {
      proof.input = "external keyboard";
      proof.initial = await observe();
      assert.equal(proof.initial.status, "Control covered");
    } else {
      for (let step = 0; step < 6; step++) {
        proof.initial = await observe();
        if (proof.initial.focus === "reveal") break;
        press("Tab");
        await delay(50);
      }
      assert.deepEqual(proof.initial, { focus: "reveal", status: "Control covered" });
    }
    const before = await capture("before");
    assert.deepEqual(before.findings, [["control-not-hittable", "r2"], ["control-clipped", "r4"]]);
    proof.before = before.findings;

    if (manualInput) {
      await writeFile(join(destination, "ready"), String(process.pid) + "\n", { flag: "wx" });
      console.log("Initial capture verified. Focus Reveal control and press Return.");
    } else {
      press("Return");
    }
    const deadline = performance.now() + (manualInput ? 120_000 : 1_500);
    while (performance.now() < deadline) {
      proof.updated = await observe();
      if (proof.updated.status === "Control revealed") break;
      await delay(50);
    }
    assert.deepEqual(proof.updated, { focus: "reveal", status: "Control revealed" });
    const after = await capture("after");
    assert.deepEqual(after.findings, [["control-clipped", "r4"]]);
    proof.after = after.findings;

    await assert.rejects(exportDesignCapture(window, before.evidencePath), { code: "EEXIST" });
    assert.equal(await readFile(before.evidencePath, "utf8"), before.evidence);
    proof.originalEvidencePreserved = true;
    if (!manualInput) {
      await window.loadURL("data:text/html,<title>Outside the local app</title>");
      const refusedPath = join(destination, "unsupported.json");
      await assert.rejects(exportDesignCapture(window, refusedPath), /Capture your app's local window/);
      await assert.rejects(readFile(refusedPath), { code: "ENOENT" });
      proof.unsupportedSourceRefused = true;
    }
    proof.passed = true;
  } catch (error) {
    proof.error = error.stack;
    process.exitCode = 1;
    console.error(error);
  } finally {
    await writeFile(join(destination, "receipt.json"), JSON.stringify(proof, null, 2) + "\n");
    if (!manualInput || !proof.passed) {
      window?.destroy();
      app.exit(process.exitCode ?? 0);
    }
  }
});
