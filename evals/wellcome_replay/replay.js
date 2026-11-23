const page = state.page;
const viewport = page.viewportSize();
const startLabel = spec.open;
const returnLabel = spec.close;
const control = page.getByRole("button",{name:startLabel,exact:true});
const checks = {uniqueAction:await control.count()===1};
const capture = path => page.screenshot({path,animations:"disabled"});
const inView = rect => !!rect && rect.y>=0 && rect.x>=0 &&
  rect.y+rect.height<=viewport.height+1 && rect.x+rect.width<=viewport.width+1;
const pumpNote = text => /pump/i.test(text) && /circle|symbol|public water/i.test(text);
const barsNote = text => /bars?|tall(?:y|ies)|marks?/i.test(text) && /deaths?/i.test(text);
const phase = async () => page.evaluate(async ({spec}) => {
  await Promise.allSettled([...document.images].map(image => image.decode()));
  const details = [];
  const source = [];
  const annotatedSource = [];
  const keys = [];
  const visible = node => node.checkVisibility({checkOpacity:true,checkVisibilityCSS:true});
  const bounds = node => {
    const {x,y,width,height} = node.getBoundingClientRect();
    return {x,y,width,height};
  };
  for (const image of document.images) {
    const box = image.getBoundingClientRect();
    if (!image.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}) || !box.width || !box.height) continue;
    const row = {x:box.x,y:box.y,width:box.width,height:box.height,fit:getComputedStyle(image).objectFit};
    const size = [image.naturalWidth,image.naturalHeight].join();
    if (size === spec.size.join()) {
      source.push(row);
      const outline = [...image.parentElement.children].find(node => {
        if (!node.matches("span[aria-hidden=true]") || !visible(node)) return false;
        const style = getComputedStyle(node);
        return style.position === "absolute" && style.borderTopStyle === "solid" &&
          parseFloat(style.borderTopWidth) >= 1;
      });
      if (outline) annotatedSource.push({image:row,outline:bounds(outline)});
    }
    if (size === spec.detail_size.join()) {
      const clip = image.parentElement;
      clip.dataset.qaFrame = "detail";
      image.dataset.qaImage = "detail";
      details.push(row);
      for (const label of clip.querySelectorAll("span[aria-hidden=true]")) {
        if (visible(label)) keys.push({label:label.textContent.trim(),...bounds(label)});
      }
    }
  }
  const notes = [];
  for (const note of document.querySelectorAll("p,li,dd,figcaption")) {
    const box = note.getBoundingClientRect();
    const text = note.textContent.replace(/\s+/g," ").trim();
    if (!note.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}) || !box.width || !box.height) continue;
    if ((/pump/i.test(text) && /circle|symbol|public water/i.test(text)) || (/bars?|tall(?:y|ies)|marks?/i.test(text) && /deaths?/i.test(text))) {
      notes.push({text,x:box.x,y:box.y,width:box.width,height:box.height});
    }
  }
  const text = document.body.innerText;
  return {source,details,notes,annotatedSource,keys,scrollY,overflow:document.documentElement.scrollWidth>innerWidth,
    credit:/Wellcome Collection/i.test(text) && /Public Domain/i.test(text) && !!document.querySelector('a[href="https://wellcomecollection.org/works/uxgfjt62"]'),
    facts:/Broad Street|Soho/i.test(text) && /John Snow/i.test(text) && /1854|1855/.test(text)};
},{spec});
const notesInView = scene => scene.notes.some(note => inView(note) && pumpNote(note.text)) &&
  scene.notes.some(note => inView(note) && barsNote(note.text));
const geometry = (row,size) => !!row &&
  (row.fit==="contain" || Math.abs(row.width/row.height-size[0]/size[1])<.02);
const project = async scene => Object.fromEntries(await Promise.all(
  Object.entries(spec.points).map(async ([name,point]) => [name,
    scene.details.length===1 ? await page.evaluate(measureImageFocus,{
      imageSelector:"[data-qa-image=detail]",clipSelector:"[data-qa-frame=detail]",
      point,region:spec.normalized_region,size:spec.detail_size
    }) : {status:"unverified",reason:"expected one visible verified crop"}
  ])
));
const verifyAnnotations = (scene,projection) => checkMapAnnotations({
  source:scene.annotatedSource,keys:scene.keys,projection,detail:scene.details[0],
  region:spec.normalized_region,viewport
});
const landmarksVisible = (scene,projection) =>
  inView(scene.details[0]) && geometry(scene.details[0],spec.detail_size) &&
  Object.values(projection).every(value=>value.status==="pass" && value.inViewport);
const report = {checks};
if (checks.uniqueAction) {
  await page.emulateMedia({reducedMotion:"no-preference"});
  const opening = await phase();
  report.opening = opening;
  const place = await control.boundingBox();
  checks.openingAction = inView(place) && place.height>=44;
  checks.openingArt = opening.source.length===1 && inView(opening.source[0]) &&
    opening.source[0].width>=150 && geometry(opening.source[0],spec.size);
  checks.closedInitially = !opening.details.length;
  checks.credits = opening.credit && opening.facts;

  await control.evaluate(node => node.dataset.qaOriginalControl = "true");
  const sameControl = page.locator("[data-qa-original-control=true]");
  const focused = () => sameControl.evaluate(node => document.activeElement===node && node.matches(":focus-visible"));
  for(let i=0; i<8 && !(await focused()); i++) await page.keyboard.press("Tab");
  checks.keyFocus = await focused();
  if (checks.keyFocus) {
    await page.keyboard.press("Enter");
    report.firstSample = await phase();
    const settled = await page.evaluate(async () => {
      const animations = document.getAnimations().filter(animation =>
        Number.isFinite(animation.effect?.getComputedTiming().endTime));
      let timer;
      try {
        return await Promise.race([
          Promise.allSettled(animations.map(animation => animation.finished)).then(() => true),
          new Promise(resolve => {timer = setTimeout(() => resolve(false),350);})
        ]);
      } finally {
        clearTimeout(timer);
      }
    });
    const open = await phase();
    report.open = open;
    checks.boundedReveal = settled && open.scrollY === report.firstSample.scrollY;
    const projection = await project(open);
    report.projection = projection;
    checks.detailReached = landmarksVisible(open,projection);
    checks.noteImmediatelyVisible = notesInView(open);
    checks.overview = open.source.some(inView);
    report.annotations = verifyAnnotations(open,projection);
    for (const key of ["locatorAccurate","compactLocator","externalKeysAligned"]) {
      checks[key] = report.annotations[key];
    }
    checks.sameFocusedReturn = await sameControl.count()===1 && await focused() &&
      await page.getByRole("button",{name:returnLabel,exact:true}).count()===1;
    checks.noOverflow = !open.overflow && !opening.overflow;
    await capture(paths.open);
    if (checks.sameFocusedReturn) await page.keyboard.press("Enter");
    const closed = await phase();
    checks.restored = closed.source.some(inView) && !closed.details.length && await focused() &&
      await page.getByRole("button",{name:startLabel,exact:true}).count()===1;
    await capture(paths.closed);
    if (checks.restored) {
      await page.emulateMedia({reducedMotion:"reduce"});
      const box = await sameControl.boundingBox();
      await page.evaluate(() => {
        window.qaTouch = false;
        document.addEventListener("pointerdown",event => {
          window.qaTouch = event.isTrusted && event.pointerType==="touch";
        },{once:true});
      });
      const tap = {x:Math.round(box.x+box.width/2),y:Math.round(box.y+box.height/2)};
      const cdp = await context.newCDPSession(page);
      await cdp.send("Input.dispatchTouchEvent",{type:"touchStart",touchPoints:[tap]});
      await cdp.send("Input.dispatchTouchEvent",{type:"touchEnd",touchPoints:[]});
      await cdp.detach();
      const motion = await page.evaluate(() => ({
        touch:window.qaTouch,
        reduced:matchMedia("(prefers-reduced-motion: reduce)").matches &&
          document.getAnimations().every(animation=>animation.effect.getComputedTiming().activeDuration<=100)
      }));
      const touch = await phase();
      const touchProjection = await project(touch);
      const touchAnnotations = verifyAnnotations(touch,touchProjection);
      report.touchAnnotations = touchAnnotations;
      checks.touch = motion.touch && landmarksVisible(touch,touchProjection) && notesInView(touch);
      checks.touchAnnotations = touchAnnotations.locatorAccurate && touchAnnotations.compactLocator &&
        touchAnnotations.externalKeysAligned;
      checks.reduced = motion.reduced;
      await capture(paths.touch);
    }
  }
}
checks.pageErrors = state.pageErrors.length===0;
checks.fullJourney = Object.keys(paths).length===3 &&
  ["restored","detailReached","noteImmediatelyVisible","touch"].every(key=>checks[key]===true);
console.log("ORDINARY "+JSON.stringify(report));
