/* Test the attribution and position of each map annotation from live CSS boxes. */
function checkMapAnnotations({source, keys, projection, detail, region, viewport}) {
  const visible = rect => rect && rect.width > 0 && rect.height > 0 &&
    rect.x >= 0 && rect.y >= 0 &&
    rect.x + rect.width <= viewport.width + 1 &&
    rect.y + rect.height <= viewport.height + 1;

  const overlap = (left, right) => {
    const width = Math.max(0, Math.min(left[0] + left[2], right[0] + right[2]) - Math.max(left[0], right[0]));
    const height = Math.max(0, Math.min(left[1] + left[3], right[1] + right[3]) - Math.max(left[1], right[1]));
    const intersection = width * height;
    return intersection / (left[2] * left[3] + right[2] * right[3] - intersection);
  };

  const locators = source.filter(({image, outline}) => visible(image) && visible(outline))
    .map(({image, outline}) => {
      const observed = [
        (outline.x - image.x) / image.width,
        (outline.y - image.y) / image.height,
        outline.width / image.width,
        outline.height / image.height
      ];
      return {observed, overlap: overlap(observed, region), overviewWidth: image.width};
    });

  const keyAlignment = Object.fromEntries([
    ["pump_circle", /^circle$/i],
    ["nearby_tallies", /^bars$/i],
  ].map(([name, label]) => {
    const point = projection[name];
    const matching = keys.filter(key => label.test(key.label));
    const key = matching.length === 1 ? matching[0] : null;
    if (!visible(key) || !point?.inViewport || !visible(detail)) {
      return [name, {pass: false, reason: "missing visible key, crop, or landmark"}];
    }
    const yError = Math.abs(key.y + key.height / 2 - point.y);
    const gap = Math.max(detail.x - key.x - key.width, key.x - detail.x - detail.width);
    return [name, {pass: yError <= Math.min(10, detail.height * 0.04) && gap >= -1 && gap <= 12,
                   yError, gap}];
  }));

  return {
    locatorAccurate: locators.some(locator => locator.overlap >= 0.80),
    compactLocator: !!detail && locators.some(locator => locator.overviewWidth <= detail.width / 2),
    externalKeysAligned: Object.values(keyAlignment).every(key => key.pass),
    locators, keyAlignment
  };
}

if (typeof module !== "undefined") module.exports = {checkMapAnnotations};
