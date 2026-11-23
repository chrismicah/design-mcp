const page = await context.newPage();
let releaseFont;
let interceptedFont;
const fontGate = new Promise(resolve => { releaseFont = resolve; });
const fontArrived = new Promise(resolve => { interceptedFont = resolve; });
let fontRequests = 0;
let fontReleased = false;
const errors = [];
try {
  page.on("pageerror", error => errors.push(String(error)));
  await page.setViewportSize({width: spec.width, height: spec.height});
  await page.route("https://fonts.googleapis.com/**", async route => {
    fontRequests += 1;
    interceptedFont();
    await fontGate;
    await route.fulfill({status: 200, contentType: "text/css", body: "/* deterministic font fixture */"});
  });
  await page.goto(spec.url, {waitUntil: "commit"});
  await Promise.race([
    fontArrived,
    new Promise((_, reject) => setTimeout(() => reject(new Error("No font stylesheet request")), 1800))
  ]);
  await page.waitForFunction(() => document.querySelector("h1") && document.querySelector("a[href^='tel:']"), null, {polling: 50, timeout: 2500});
  await new Promise(resolve => setTimeout(resolve, 500));
  await page.keyboard.press("Tab");
  const inspect = () => {
    const link = document.querySelector("a[href^='tel:']");
    const heading = document.querySelector("h1");
    function inside(node) {
      const box = node.getBoundingClientRect();
      return box.x >= 0 && box.y >= 0 && box.right <= innerWidth &&
        box.bottom <= innerHeight && box.height > 0 && box.width > 0;
    }
    return {
      elapsed_ms: performance.now(),
      first_contentful_paint_ms: performance.getEntriesByName("first-contentful-paint")[0]?.startTime ?? null,
      call_focused: document.activeElement === link,
      call_in_view: inside(link),
      call_label: link.innerText.trim(),
      heading_in_view: inside(heading),
      heading: heading.innerText.trim(),
      viewport_width: innerWidth,
    };
  };
  const held = await page.evaluate(inspect);
  const pending = fontRequests === 1 && !fontReleased;
  fontReleased = true;
  releaseFont();
  await page.waitForLoadState("load");
  await page.waitForFunction(() => performance.getEntriesByName("first-contentful-paint").length === 1);
  const released = await page.evaluate(inspect);
  await page.screenshot({path: spec.shot, animations: "disabled"});
  console.log("STARTUP_RESULT " + JSON.stringify({held, released, pending, fontRequests, errors}));
} finally {
  releaseFont();
  await page.close();
}
