import { writeFile } from "node:fs/promises";

function collect() {
  const viewport = [innerWidth, innerHeight];
  const selector = "button, a[href], input, select, textarea, [role=button], [role=switch], [role=slider]";
  const roles = { BUTTON: "button", A: "link", SELECT: "selector", TEXTAREA: "input", INPUT: "input" };
  const regions = [];
  for (const node of document.querySelectorAll(selector)) {
    if (regions.length >= 80) break;
    if (node.matches(":disabled, [aria-disabled=true]") || node.closest("[hidden], [inert], [aria-hidden=true]")) continue;
    const rect = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    if (!rect.width || !rect.height || style.visibility !== "visible" || style.display === "none" ||
        rect.right <= 0 || rect.bottom <= 0 || rect.x >= innerWidth || rect.y >= innerHeight) continue;
    const x = Math.max(0, Math.min(innerWidth - 1, rect.x + rect.width / 2));
    const y = Math.max(0, Math.min(innerHeight - 1, rect.y + rect.height / 2));
    const hit = document.elementFromPoint(x, y);
    const role = { switch: "toggle", slider: "slider", button: "button" }[node.getAttribute("role")];
    regions.push({ id: "r" + (regions.length + 1), role: role || roles[node.tagName],
      bounds: [rect.x, rect.y, rect.width, rect.height], hittable: Boolean(hit && node.contains(hit)) });
  }
  return { version: 1, platform: "electron", viewport, regions };
}

function allowed(url) {
  return url.protocol === "file:" || ((url.protocol === "http:" || url.protocol === "https:") &&
    ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname));
}

export async function exportDesignCapture(window, outputFile) {
  const contents = window.webContents;
  const source = contents.getURL();
  if (!allowed(new URL(source))) throw new Error("Capture your app's local window.");
  let changed = false;
  const markNavigation = () => { changed = true; };
  contents.on("did-start-navigation", markNavigation);
  try {
    const sample = await contents.executeJavaScriptInIsolatedWorld(1001, [{ code: "(" + collect.toString() + ")()" }]);
    if (changed || contents.isDestroyed() || contents.getURL() !== source) {
      throw new Error("The app navigated during capture. Try again once the window settles.");
    }
    await writeFile(outputFile, JSON.stringify(sample) + "\n", { encoding: "utf8", flag: "wx", mode: 0o600 });
    return sample.regions.length;
  } finally {
    contents.removeListener("did-start-navigation", markNavigation);
  }
}
