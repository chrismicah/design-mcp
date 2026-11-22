import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { app, BrowserWindow } from "electron";
import { exportDesignCapture } from "../../integrations/desktop/electron.mjs";

const [cli, destination] = process.argv.slice(-2);
const fixture = fileURLToPath(new URL("fixtures/electron-review.html", import.meta.url));

await mkdir(destination, { recursive: true });
app.setPath("userData", join(destination, "isolated-user-data"));
const proof = { electron: process.versions.electron, platform: process.platform };
let window;

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
  const image = await window.webContents.capturePage();
  assert.equal(image.isEmpty(), false);
  assert.deepEqual(image.getSize(), { width: 880, height: 640 });
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
    const windowId = execFileSync("xdotool", ["search", "--onlyvisible", "--name", "^Desk review fixture$"],
      { encoding: "utf8" }).trim().split("\n").at(-1);
    execFileSync("xdotool", ["windowfocus", "--sync", windowId]);
    const observe = () => window.webContents.executeJavaScript(
      "({ focus: document.activeElement.id, status: document.querySelector('#status').textContent })"
    );

    proof.initial = await observe();
    assert.deepEqual(proof.initial, { focus: "reveal", status: "Control covered" });
    const before = await capture("before");
    assert.deepEqual(before.findings, [["control-not-hittable", "r2"], ["control-clipped", "r4"]]);
    proof.before = before.findings;

    execFileSync("xdotool", ["key", "--clearmodifiers", "Return"]);
    for (let step = 0; step < 30; step++) {
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
    await window.loadURL("data:text/html,<title>Outside the local app</title>");
    const refusedPath = join(destination, "unsupported.json");
    await assert.rejects(exportDesignCapture(window, refusedPath), /Capture your app's local window/);
    await assert.rejects(readFile(refusedPath), { code: "ENOENT" });
    proof.unsupportedSourceRefused = true;
    proof.passed = true;
  } catch (error) {
    proof.error = error.stack;
    process.exitCode = 1;
    console.error(error);
  } finally {
    await writeFile(join(destination, "receipt.json"), JSON.stringify(proof, null, 2) + "\n");
    window?.destroy();
    app.exit(process.exitCode ?? 0);
  }
});
