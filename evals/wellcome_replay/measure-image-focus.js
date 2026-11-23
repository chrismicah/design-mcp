/* Evaluate in the fixture document after opening the detail.
 * Coordinates are normalized against the master image, independent of DPR.
 * This checks geometry for unmasked, axis-aligned images. Review pixels for
 * overlays, content identity, and feature legibility.
 */
async function measureImageFocus({imageSelector, clipSelector, point, region, size, inset = 6}) {
  const unverified = reason => ({status: "unverified", reason});
  if (!Array.isArray(point) || point.length !== 2 ||
      !Array.isArray(region) || region.length !== 4 ||
      ![...point,...region,inset].every(Number.isFinite) ||
      point.some(value => value < 0 || value > 1) || region.some(value => value < 0) ||
      region[2] <= 0 || region[3] <= 0 || region[0] + region[2] > 1.000001 ||
      region[1] + region[3] > 1.000001 || inset < 0) return unverified("invalid-coordinates");
  let images, clips;
  try {
    images = document.querySelectorAll(imageSelector);
    clips = document.querySelectorAll(clipSelector);
  } catch {
    return unverified("invalid-selector");
  }
  if (images.length !== 1 || !(images[0] instanceof HTMLImageElement) || clips.length !== 1 ||
      !clips[0].contains(images[0])) return unverified("ambiguous-image-or-clip");
  const img = images[0];
  const clip = clips[0];
  try { await img.decode(); } catch { return unverified("image-decode-failed"); }
  if (!size || img.naturalWidth !== size[0] || img.naturalHeight !== size[1]) {
    return unverified("unexpected-image-size");
  }
  const style = getComputedStyle(img);
  for (let element = img; element; element = element.parentElement) {
    const css = getComputedStyle(element);
    const matrix = new DOMMatrixReadOnly(css.transform === "none" ? undefined : css.transform);
    if (!matrix.is2D || matrix.b !== 0 || matrix.c !== 0 || matrix.a <= 0 || matrix.d <= 0 ||
        css.rotate !== "none" || css.scale !== "none" || css.clipPath !== "none" ||
        css.maskImage !== "none" || css.clip !== "auto" ||
        css.visibility !== "visible" || Number(css.opacity) === 0) return unverified("unsupported-image-geometry");
  }
  const position = style.objectPosition.split(/\s+/);
  if (position.length !== 2 || !position.every(part => /^-?[\d.]+%$/.test(part)) ||
      ["paddingTop","paddingBottom","paddingLeft","paddingRight","borderTopWidth","borderBottomWidth",
       "borderLeftWidth","borderRightWidth"].some(key => parseFloat(style[key]) !== 0)) {
    return unverified("unsupported-image-box");
  }
  const box = img.getBoundingClientRect();
  if (box.width <= 0 || box.height <= 0 || img.clientWidth <= 0 || img.clientHeight <= 0) {
    return unverified("image-not-rendered");
  }
  const pixelX = box.width / img.clientWidth;
  const pixelY = box.height / img.clientHeight;
  const scales = [img.clientWidth / img.naturalWidth, img.clientHeight / img.naturalHeight];
  let width = box.width;
  let height = box.height;
  if (style.objectFit !== "fill") {
    const factors = {cover:Math.max(...scales), contain:Math.min(...scales), none:1,
                     "scale-down":Math.min(1,...scales)};
    const scale = factors[style.objectFit];
    if (!scale) return unverified("unsupported-fit");
    width = img.naturalWidth * scale * pixelX;
    height = img.naturalHeight * scale * pixelY;
  }
  const u = (point[0] - region[0]) / region[2];
  const v = (point[1] - region[1]) / region[3];
  if (u < 0 || u > 1 || v < 0 || v > 1) return {status:"fail",reason:"outside-source-region"};
  const x = box.left + (box.width - width) * parseFloat(position[0]) / 100 + width * u;
  const y = box.top + (box.height - height) * parseFloat(position[1]) / 100 + height * v;
  const limits = {left:box.left,right:box.right,top:box.top,bottom:box.bottom};
  for (let element = img.parentElement; element; element = element.parentElement) {
    const css = getComputedStyle(element);
    if (element === clip || css.overflowX !== "visible" || css.overflowY !== "visible") {
      if (element === document.documentElement && element !== clip) break;
      if (["borderTopLeftRadius","borderTopRightRadius","borderBottomRightRadius","borderBottomLeftRadius"]
          .some(key => parseFloat(css[key]) !== 0)) return unverified("non-rectangular-clip");
      const rect = element.getBoundingClientRect();
      const scaleX = element.offsetWidth ? rect.width / element.offsetWidth : 1;
      const scaleY = element.offsetHeight ? rect.height / element.offsetHeight : 1;
      const left = rect.left + element.clientLeft * scaleX;
      const top = rect.top + element.clientTop * scaleY;
      if (element === clip || css.overflowX !== "visible") {
        limits.left = Math.max(limits.left,left);
        limits.right = Math.min(limits.right,left + element.clientWidth * scaleX);
      }
      if (element === clip || css.overflowY !== "visible") {
        limits.top = Math.max(limits.top,top);
        limits.bottom = Math.min(limits.bottom,top + element.clientHeight * scaleY);
      }
    }
  }
  const clearance = Math.min(x-limits.left, limits.right-x, y-limits.top, limits.bottom-y);
  return {status:clearance >= inset ? "pass" : "fail", x,y,clearance,
          inViewport:x>=0 && x<innerWidth && y>=0 && y<innerHeight, limits};
}
