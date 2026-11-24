'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const {createContext, runInContext} = require('node:vm');

const extension = join(__dirname, '../../design_mcp/review/extension');
const popup = readFileSync(join(extension, 'popup.js'), 'utf8');
const collector = readFileSync(join(extension, 'collector.js'), 'utf8');

function fixture(change) {
  const tab = {id: 7, windowId: 3, url: 'https://example.test/form', title: 'Form'};
  const field = y => ({kind: 'field', box: {x: 0.1, y, width: 0.4, height: 0.08}});
  const frame = (boxes, scrollY = 0) => ({
    document: {scroll_width: 800, client_width: 800, lang: 'en', scroll_x: 0, scroll_y: scrollY},
    viewport: {width: 800, height: 600, dpr: 1},
    masks: {applied: false, boxes},
  });
  const frames = [
    frame([field(0.2)]),
    frame(
      change === 'new-field' ? [field(0.2), field(0.4)] : [field(change === 'reflow' ? 0.3 : 0.2)],
      change === 'scroll' ? 10 : 0,
    ),
  ];
  if (change === 'reflow') frames.push(frame([field(0.3)]), frame([field(0.3)]));
  const elements = new Map();
  const sends = [];
  const document = {
    body: {dataset: {}},
    getElementById(id) {
      if (!elements.has(id)) {
        elements.set(id, {dataset: {}, addEventListener() {}, focus() { document.focused = id; }});
      }
      return elements.get(id);
    },
  };
  let queries = 0;
  const context = createContext({
    URL, URLSearchParams, document, location: {search: ''},
    localStorage: {getItem: () => null, setItem() {}},
    PerformanceObserver: class { observe() {} }, performance: {now: () => 0},
    chrome: {
      runtime: {async sendNativeMessage(host, packet) {
        sends.push({host, packet});
        return {ok: true, regions: 1, message: 'No findings.'};
      }},
      tabs: {
        async query() {
          queries += 1;
          return [change === 'tab' && queries === 2 ? {...tab, id: 8} : tab];
        },
        async captureVisibleTab() { return 'data:image/png;base64,AA=='; },
      },
      scripting: {async executeScript({func}) {
        const oldViewportProbe = [0, change === 'scroll' ? 10 : 0, 800, 600];
        return [{result: func.name === 'designMcpCollect' ? frames.shift() : oldViewportProbe}];
      }},
    },
    maskPagePicture: async (_picture, boxes) => 'masked:' + boxes.length,
  });
  runInContext(collector, context);
  runInContext(popup + '\nthis.scanForTest = scan;', context);
  return {scan: context.scanForTest, document, sends};
}

test('a stable active tab hands off exactly one masked frame', async () => {
  const {scan, sends, document} = fixture('stable');
  assert.equal(sends.length, 0);
  await scan();
  assert.equal(sends.length, 1);
  assert.equal(sends[0].host, 'com.design_mcp.review');
  assert.equal(sends[0].packet.type, 'review');
  const [frame] = sends[0].packet.bundle.frames;
  assert.equal(frame.masks.applied, true);
  assert.equal(frame.masks.boxes.length, 1);
  assert.equal(frame.screenshot.data, 'masked:1');
  assert.equal(document.body.dataset.state, 'result');
  assert.equal(document.focused, 'open');
});

for (const change of ['reflow', 'new-field', 'scroll', 'tab']) {
  test(`a ${change} change returns focus to Scan and sends no capture`, async () => {
    const {scan, sends, document} = fixture(change);
    await scan();
    assert.equal(sends.length, 0);
    assert.equal(document.body.dataset.state, 'problem');
    assert.match(document.getElementById('status').textContent, /page moved or the tab changed/);
    assert.equal(document.getElementById('result').hidden, true);
    assert.equal(document.getElementById('scan').disabled, false);
    assert.equal(document.focused, 'scan');
  });
}

test('a fresh scan succeeds once the form stops moving', async () => {
  const {scan, sends, document} = fixture('reflow');
  await scan();
  assert.equal(sends.length, 0);
  await scan();
  assert.equal(sends.length, 1);
  const [frame] = sends[0].packet.bundle.frames;
  assert.equal(frame.masks.boxes[0].box.y, 0.3);
  assert.equal(frame.masks.applied, true);
  assert.equal(document.body.dataset.state, 'result');
});
