const assert = require("node:assert/strict");
const {test} = require("node:test");
const {checkMapAnnotations} = require("./map-annotation-geometry.js");

const fixture = {
  source: [{image: {x: 23, y: 582, width: 100, height: 92},
            outline: {x: 73, y: 619, width: 16, height: 14}}],
  keys: [{label: "Circle", x: 8, y: 181, width: 44, height: 12},
         {label: "Bars", x: 13, y: 236, width: 39, height: 12}],
  projection: {pump_circle: {y: 187, inViewport: true}, nearby_tallies: {y: 242, inViewport: true}},
  detail: {x: 53, y: 68, width: 266, height: 290},
  region: [0.496, 0.404, 0.158, 0.148],
  viewport: {width: 390, height: 844},
};

test("the accurate compact outline and separate outside keys qualify", () => {
  const result = checkMapAnnotations(fixture);
  assert.equal(result.locatorAccurate, true);
  assert.equal(result.compactLocator, true);
  assert.equal(result.externalKeysAligned, true);
});

test("a visible box at the wrong site does not count", () => {
  const shifted = structuredClone(fixture);
  shifted.source[0].outline.x += 18;
  assert.equal(checkMapAnnotations(shifted).locatorAccurate, false);
});

test("outside labels need visible, separately aligned marks", () => {
  const shifted = structuredClone(fixture);
  shifted.keys[1].y = shifted.keys[0].y;
  assert.equal(checkMapAnnotations(shifted).externalKeysAligned, false);
  shifted.keys[1] = {...fixture.keys[1], x: 20};
  assert.equal(checkMapAnnotations(shifted).externalKeysAligned, false);
  shifted.keys[1] = {...fixture.keys[1], x: -2};
  assert.equal(checkMapAnnotations(shifted).externalKeysAligned, false);
});
