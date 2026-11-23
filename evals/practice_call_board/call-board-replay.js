const page = state.page;
await page.emulateMedia({reducedMotion: "no-preference"});
const viewport = page.viewportSize();
const match = pattern => new RegExp(pattern, "i");
const radio = label => page.getByRole("radio", {name: label, exact: true});
const alternate = radio(practice.alternateService);
const service = page.getByRole("combobox", {name: match(practice.selectLabel)});
const name = page.getByRole("textbox", {name: match(practice.nameLabel)});
const preview = page.getByRole("button", {name: match(practice.previewLabel)});
const draft = page.getByRole("textbox", {name: match(practice.resultLabel)});
const resultHeading = page.getByRole("heading", {name: match(practice.resultLabel)});
const contact = page.getByRole("link", {name: match(practice.contactLabel)});
const nativeSelect = await service.count() === 1;
const firstService = nativeSelect ? service : radio(practice.firstService);
async function alternateSelected() {
  if (!nativeSelect) return alternate.isChecked();
  return service.evaluate((node, expected) => node.selectedOptions[0]?.label.trim() === expected,
    practice.alternateService);
}
const requests = [];
page.on("request", request => requests.push(request.method()));
const active = async control => await control.evaluate(node => node === document.activeElement);
async function reach(control, key = "Tab") {
  if (await control.count() !== 1) return false;
  for (let tabs = 0; tabs < 10; tabs++) {
    if (await active(control)) return true;
    await page.keyboard.press(key);
  }
  return false;
}

const opening = await page.evaluate(phone => {
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
    return digits === phone || digits === "1" + phone;
  });
  const box = dial?.getBoundingClientRect();
  return {text: text.join(" "), dial: !!box && box.height >= 44 && box.y >= 0 && box.bottom <= innerHeight};
}, practice.phone);
const inView = box => !!box && box.x >= 0 && box.y >= 0 &&
  box.x + box.width <= viewport.width + 1 && box.y + box.height <= viewport.height + 1;
const initialForm = {name: await name.boundingBox(), preview: await preview.boundingBox()};
const visibleServiceChoices = practice.allowVisibleServicePicker && nativeSelect &&
  inView(await service.boundingBox()) &&
  await service.evaluate((node, labels) => {
    const options = [...node.options].map(option => option.label.trim());
    return labels.every(label => options.includes(label));
  }, [practice.firstService, practice.alternateService]);
const checks = {
  nameInitiallyVisible: inView(initialForm.name),
  previewInitiallyVisible: inView(initialForm.preview),
  openingIdentity: practice.identity.every(pattern => match(pattern).test(opening.text)),
  openingHours: practice.hours.every(pattern => match(pattern).test(opening.text)),
  openingServices: Boolean(visibleServiceChoices) || practice.services.every(pattern => match(pattern).test(opening.text)),
  openingPhone: opening.dial,
  openingWidth: await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  normalMotion: await page.evaluate(() => matchMedia("(prefers-reduced-motion: no-preference)").matches),
};

checks.contactFocus = await contact.count() === 1 && await reach(contact);
checks.reachService = await reach(firstService);
if (checks.reachService) {
  await page.keyboard.press(nativeSelect ? practice.alternateService[0].toLowerCase() : "ArrowRight");
}
checks.serviceSelected = await alternateSelected() && await active(nativeSelect ? service : alternate);
checks.reachPreview = await reach(preview);
if (checks.reachPreview) await page.keyboard.press("Enter");
checks.emptyNameRecovery = await active(name) && await name.getAttribute("aria-invalid") === "true";
checks.errorVisible = await page.getByText(/enter your first name/i).isVisible();
checks.selectionAfterError = await alternateSelected();
await page.screenshot({path: paths.invalid, animations: "disabled"});
if (checks.emptyNameRecovery) {
  await page.evaluate(disclosurePattern => {
    const form = document.querySelector("form");
    form.addEventListener("submit", () => {
      requestAnimationFrame(() => {
        const focus = document.activeElement;
        const textAreas = [...document.querySelectorAll("textarea")].filter(el => el.checkVisibility());
        const box = textAreas.length === 1 ? textAreas[0].getBoundingClientRect() : null;
        window.qaOpeningFrame = {
          focusTag: focus?.tagName,
          focusLabel: (focus?.innerText || "").trim().slice(0, 120),
          editable: box && {x: box.x, y: box.y, width: box.width, height: box.height}
        };
        if (disclosurePattern) {
          window.qaOpeningFrame.focusIsEditable = textAreas.length === 1 && focus === textAreas[0];
          const disclosure = new RegExp(disclosurePattern, "i");
          const text = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          window.qaOpeningFrame.localDisclosureVisible = false;
          for (let node = text.nextNode(); box && node; node = text.nextNode()) {
            if (!disclosure.test(node.textContent) ||
                !node.parentElement.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) continue;
            const range = document.createRange();
            range.selectNodeContents(node);
            const rect = range.getBoundingClientRect();
            if (rect.width && rect.height && rect.x >= 0 && rect.y >= 0 &&
                rect.right <= innerWidth + 1 && rect.bottom <= innerHeight + 1 &&
                Math.abs(rect.y - box.y) <= Math.min(300, innerHeight / 2)) {
              window.qaOpeningFrame.localDisclosureVisible = true;
              break;
            }
          }
        }
      });
    }, {once: true});
  }, practice.recordEditorFocus ? practice.localDisclosure : null);
  await page.keyboard.type(practice.visitorName);
  if (await reach(preview)) await page.keyboard.press("Enter");
}
const headingFocused = await resultHeading.count() === 1 && await active(resultHeading);
checks.previewFocused = await draft.isVisible() && (await active(draft) || headingFocused);
const draftText = await draft.isVisible() ? (await draft.inputValue()).toLowerCase() : "";
checks.previewReady = draftText.includes(practice.visitorName.toLowerCase()) &&
  draftText.includes(practice.alternateService.toLowerCase());
if (checks.previewReady) {
  await page.waitForFunction(() => Boolean(window.qaOpeningFrame), undefined, {timeout: 1500});
}
const firstFrame = await page.evaluate(() => window.qaOpeningFrame || null);
if (practice.recordEditorFocus) {
  checks.editorFocusedInFirstFrame = firstFrame?.focusIsEditable === true && await draft.count() === 1;
  checks.disclosureVisibleInFirstFrame = firstFrame?.localDisclosureVisible === true;
}
checks.previewInFirstViewport = inView(firstFrame?.editable) &&
  firstFrame.editable.width > 0 && firstFrame.editable.height > 0;
checks.statusAnnouncement = await page.getByRole("status").count() === 1 &&
  /reminder|draft|note/i.test(await page.getByRole("status").innerText());
// Visible text near the draft must say that the result stays local or sends nothing.
const disclosure = await page.getByText(match(practice.localDisclosure)).all();
const draftBox = await draft.boundingBox();
const disclosures = await Promise.all(disclosure.map(label => label.boundingBox()));
checks.honestResultVisible = Boolean(draftBox && disclosures.some(box => inView(box) &&
  Math.abs(box.y - draftBox.y) <= Math.min(300, viewport.height / 2)));
if (checks.previewReady) {
  await page.screenshot({path: paths.preview, animations: "disabled"});
}
checks.reachEditableDraft = checks.previewReady && await reach(draft);
if (checks.reachEditableDraft) {
  await page.keyboard.press("End");
  await page.keyboard.type(" I can call Thursday.");
}
checks.editableDraft = checks.reachEditableDraft && /I can call Thursday\./.test(await draft.inputValue());
let reachedOriginal = false;
if (checks.previewReady) {
  const back = practice.returnLabel && page.getByRole("button", {name: match(practice.returnLabel)});
  if (back && await back.count() === 1 && await back.isVisible() && await reach(back)) {
    await page.keyboard.press("Enter");
  }
  reachedOriginal = await reach(name, "Shift+Tab");
}
checks.returnToOriginal = reachedOriginal &&
  await name.inputValue() === practice.visitorName && await alternateSelected();
checks.noNetworkSubmission = !requests.some(method => method !== "GET");
checks.noPageErrors = state.pageErrors.length === 0;
checks.finalWidth = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
const finalFocus = await page.evaluate(() => (document.activeElement?.labels?.[0]?.textContent || "").trim());
const receipt = {checks, viewport, finalFocus, requests, firstFrame, initialForm};
if (practice.recordEditorFocus) {
  receipt.statusAfterReturn = (await page.getByRole("status").allTextContents()).map(text => text.trim());
}
console.log("PRACTICE_REPLAY " + JSON.stringify(receipt));
