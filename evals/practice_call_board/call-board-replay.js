const page = state.page;
await page.emulateMedia({reducedMotion: "no-preference"});
const viewport = page.viewportSize();
const glasses = page.getByRole("radio", {name: "Glasses fitting", exact: true});
const eyeExam = page.getByRole("radio", {name: "Eye exam", exact: true});
const service = page.getByRole("combobox", {name: "Service", exact: true});
const name = page.getByRole("textbox", {name: "First name", exact: true});
const preview = page.getByRole("button", {name: "Preview reminder", exact: true});
const draft = page.getByRole("textbox", {name: /^(your )?(editable )?reminder$/i});
const nativeSelect = await service.count() === 1;
const firstService = nativeSelect ? service : eyeExam;
async function fittingSelected() {
  return nativeSelect ? (await service.inputValue()) === "Glasses fitting" : await glasses.isChecked();
}
const requests = [];
page.on("request", request => requests.push(request.method()));
const active = async control => await control.evaluate(node => node === document.activeElement);
async function reach(control, key = "Tab") {
  for (let tabs = 0; tabs < 10; tabs++) {
    if (await active(control)) return true;
    await page.keyboard.press(key);
  }
  return false;
}

const opening = await page.evaluate(() => {
  const text = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let node = walk.nextNode(); node; node = walk.nextNode()) {
    const parent = node.parentElement;
    if (!parent.checkVisibility({checkOpacity: true, checkVisibilityCSS: true}) || !node.textContent.trim()) continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rect = range.getBoundingClientRect();
    if (rect.width && rect.height && rect.x >= 0 && rect.y >= 0 && rect.right <= innerWidth + 1 && rect.bottom <= innerHeight) {
      text.push(node.textContent.trim());
    }
  }
  const dial = [...document.querySelectorAll("a[href^='tel:']")].find(link => {
    const digits = link.getAttribute("href").replace(/\D/g, "");
    return digits === "2535550143" || digits === "12535550143";
  });
  const box = dial?.getBoundingClientRect();
  return {text: text.join(" "), dial: !!box && box.height >= 44 && box.y >= 0 && box.bottom <= innerHeight};
});
const inView = box => !!box && box.x >= 0 && box.y >= 0 &&
  box.x + box.width <= viewport.width + 1 && box.y + box.height <= viewport.height + 1;
const initialForm = {name: await name.boundingBox(), preview: await preview.boundingBox()};
const checks = {
  nameInitiallyVisible: inView(initialForm.name),
  previewInitiallyVisible: inView(initialForm.preview),
  openingIdentity: /Lena Ortiz/i.test(opening.text) && /optometrist/i.test(opening.text) && /Tacoma/i.test(opening.text),
  openingHours: /9 am.{1,5}4 pm/i.test(opening.text) && /Tuesday through Saturday/i.test(opening.text),
  openingServices: /eye exams?/i.test(opening.text) && /glasses fittings?/i.test(opening.text),
  openingPhone: opening.dial,
  openingWidth: await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  normalMotion: await page.evaluate(() => matchMedia("(prefers-reduced-motion: no-preference)").matches),
};

checks.contactFocus = await page.getByRole("link", {name: /Call 253-555-0143/i}).count() === 1 &&
  await reach(page.getByRole("link", {name: /Call 253-555-0143/i}));
checks.reachService = await reach(firstService);
if (checks.reachService) {
  await page.keyboard.press(nativeSelect ? "g" : "ArrowRight");
}
checks.serviceSelected = await fittingSelected() && await active(nativeSelect ? service : glasses);
checks.reachPreview = await reach(preview);
if (checks.reachPreview) await page.keyboard.press("Enter");
checks.emptyNameRecovery = await active(name) && await name.getAttribute("aria-invalid") === "true";
checks.errorVisible = await page.getByText(/enter your first name/i).isVisible();
checks.selectionAfterError = await fittingSelected();
await page.screenshot({path: paths.invalid, animations: "disabled"});
if (checks.emptyNameRecovery) {
  await page.evaluate(() => {
    const form = document.querySelector("form");
    form.addEventListener("submit", () => {
      requestAnimationFrame(() => {
        const node = document.activeElement;
        const rect = node?.getBoundingClientRect();
        window.qaOpeningFrame = {tag: node?.tagName, top: rect?.top, bottom: rect?.bottom, height: innerHeight};
      });
    }, {once: true});
  });
  await page.keyboard.type("Morgan");
  if (await reach(preview)) await page.keyboard.press("Enter");
}
checks.previewFocused = await draft.isVisible() && await active(draft);
checks.previewReady = checks.previewFocused && /Morgan.*glasses fitting/i.test(await draft.inputValue());
if (checks.previewFocused) {
  await page.waitForFunction(() => Boolean(window.qaOpeningFrame), undefined, {timeout: 1500});
}
const firstFrame = await page.evaluate(() => window.qaOpeningFrame || null);
checks.previewInFirstViewport = firstFrame?.tag === "TEXTAREA" &&
  firstFrame.top >= 0 && firstFrame.bottom <= firstFrame.height + 1;
checks.statusAnnouncement = await page.getByRole("status").count() === 1 &&
  /reminder|draft/i.test(await page.getByRole("status").innerText());
const honest = page.getByText(/Nothing was sent or booked/i);
checks.honestResultVisible = await honest.count() === 1 && inView(await honest.boundingBox());
if (checks.previewReady) {
  await page.screenshot({path: paths.preview, animations: "disabled"});
  await page.keyboard.press("End");
  await page.keyboard.type(" I can call Thursday.");
}
checks.editableDraft = checks.previewReady && /I can call Thursday\./.test(await draft.inputValue());
checks.returnToOriginal = checks.previewReady && await reach(name, "Shift+Tab") &&
  await name.inputValue() === "Morgan" && await fittingSelected();
checks.noNetworkSubmission = !requests.some(method => method !== "GET");
checks.noPageErrors = state.pageErrors.length === 0;
checks.finalWidth = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
const finalFocus = await page.evaluate(() => (document.activeElement?.labels?.[0]?.textContent || "").trim());
console.log("PRACTICE_REPLAY " + JSON.stringify({checks, viewport, finalFocus, requests, firstFrame, initialForm}));
