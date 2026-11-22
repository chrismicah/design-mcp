'use strict';

/* The popup does nothing until a button is pressed: no request, no page access, no message to the
   local reviewer. Pressing "Review this page" reads the visible part of the active tab, blanks out
   fields in the picture, and hands the capture to the local reviewer on this computer. */

const HOST = 'com.design_mcp.review';
const SCHEMA = 'design-mcp.page-evidence/1';
const MASK_COLOR = '#8a8f98';
const IDLE_TEXT = 'Scans only what you can see in this tab. Form fields are blanked out. Nothing is uploaded.';
const el = id => document.getElementById(id);

// Timings stay in this extension's own storage so 30 opens and 30 scans can be read back and reported.
function remember(kind, ms) {
  try {
    const all = JSON.parse(localStorage.getItem('dm.timings') || '{}');
    all[kind] = (all[kind] || []).concat(Math.round(ms)).slice(-30);
    localStorage.setItem('dm.timings', JSON.stringify(all));
  } catch (error) { /* timing is optional */ }
}

try {
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      if (entry.name === 'first-contentful-paint') remember('open', entry.startTime);
    }
  }).observe({type: 'paint', buffered: true});
} catch (error) { /* paint timing is optional */ }

function show(state, text, command) {
  document.body.dataset.state = state;
  el('status').textContent = text;
  el('command-text').textContent = command || '';
  el('command').hidden = !command;
}

function problem(text, command) {
  const error = new Error(text);
  error.shown = true;
  error.command = command || '';
  return error;
}

function hostProblem(error) {
  const text = String((error && error.message) || error);
  const command = 'design-mcp review --install-host ' + chrome.runtime.id;
  if (/not found/i.test(text)) {
    return problem('One step left: connect the local reviewer. Run this in a terminal, then press the button again.', command);
  }
  if (/forbidden/i.test(text)) {
    return problem('The local reviewer is connected to a different copy of this extension. Run this in a terminal, then press the button again.', command);
  }
  return problem('The local reviewer stopped before answering, so there is no result. Check that design-mcp is installed, run this in a terminal, then press the button again.', command);
}

// Paint over fields, editable areas and embedded frames before the picture is stored or sent anywhere.
async function blankOut(dataUrl, boxes) {
  if (!boxes.length) return dataUrl.slice(dataUrl.indexOf(',') + 1);
  const image = new Image();
  image.src = dataUrl;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const pen = canvas.getContext('2d');
  pen.drawImage(image, 0, 0);
  pen.fillStyle = MASK_COLOR;
  for (const item of boxes) {
    pen.fillRect(
      Math.floor(item.box.x * canvas.width) - 1, Math.floor(item.box.y * canvas.height) - 1,
      Math.ceil(item.box.width * canvas.width) + 2, Math.ceil(item.box.height * canvas.height) + 2);
  }
  const masked = canvas.toDataURL('image/png');
  return masked.slice(masked.indexOf(',') + 1);
}

// Show the affected part of the capture itself, outlined, with a little of the page around it.
async function drawRegion(base64, box) {
  const canvas = el('where');
  canvas.hidden = true;
  if (!box) return;
  const image = new Image();
  image.src = 'data:image/png;base64,' + base64;
  await image.decode();
  const pad = 0.04;
  const left = Math.max(0, box.x - pad);
  const top = Math.max(0, box.y - pad);
  const right = Math.min(1, box.x + box.width + pad);
  const bottom = Math.min(1, box.y + box.height + pad);
  const sw = (right - left) * image.naturalWidth;
  const sh = (bottom - top) * image.naturalHeight;
  const ratio = window.devicePixelRatio || 1;
  const cssWidth = 336;
  canvas.width = Math.round(cssWidth * ratio);
  canvas.height = Math.round(Math.max(48, Math.min(168, cssWidth * sh / sw)) * ratio);
  const fit = Math.min(canvas.width / sw, canvas.height / sh);
  const dx = (canvas.width - sw * fit) / 2;
  const dy = (canvas.height - sh * fit) / 2;
  const pen = canvas.getContext('2d');
  pen.fillStyle = '#ffffff';
  pen.fillRect(0, 0, canvas.width, canvas.height);
  pen.drawImage(image, left * image.naturalWidth, top * image.naturalHeight, sw, sh, dx, dy, sw * fit, sh * fit);
  pen.lineWidth = 2 * ratio;
  pen.strokeStyle = '#b4235a';
  pen.strokeRect(
    dx + (box.x - left) * image.naturalWidth * fit, dy + (box.y - top) * image.naturalHeight * fit,
    box.width * image.naturalWidth * fit, box.height * image.naturalHeight * fit);
  canvas.hidden = false;
}

function storedAddress(url) {
  const address = new URL(url);
  address.hash = '';
  address.username = '';
  address.password = '';
  return address.href;
}

function wasPasted(url) {
  try {
    const address = new URL(url);
    return localStorage.getItem('dm.pasted') === address.origin + address.pathname;
  } catch (error) {
    return false;
  }
}

async function capture() {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  if (!tab || !/^https?:\/\//i.test(tab.url || '')) {
    throw problem('This page cannot be scanned. Browser pages, the extension store and local files are off limits. Open a normal web page and press the button again.');
  }
  let frame;
  try {
    const injected = await chrome.scripting.executeScript({
      target: {tabId: tab.id}, func: designMcpCollect, args: [{maxRegions: 8}],
    });
    frame = injected && injected[0] && injected[0].result;
  } catch (error) {
    throw problem('Chrome did not allow reading this page, so nothing was read. Some pages are always off limits to extensions.');
  }
  if (!frame) throw problem('The page gave nothing back. Reload it and press the button again.');

  let picture;
  let probe;
  try {
    picture = await chrome.tabs.captureVisibleTab(tab.windowId, {format: 'png'});
    [probe] = await chrome.scripting.executeScript({
      target: {tabId: tab.id},
      func: () => [Math.round(window.scrollX), Math.round(window.scrollY), window.innerWidth, window.innerHeight],
    });
  } catch (error) {
    throw problem('Chrome did not allow a picture of this tab, so nothing was saved. Press the button again.');
  }
  const [still] = await chrome.tabs.query({active: true, currentWindow: true});
  const before = [frame.document.scroll_x, frame.document.scroll_y, frame.viewport.width, frame.viewport.height];
  if (!still || still.id !== tab.id || still.url !== tab.url || !probe || String(probe.result) !== String(before)) {
    throw problem('The page moved or the tab changed during the scan, so nothing was saved. Leave the page still for a second and press the button again.');
  }

  frame.screenshot = {media_type: 'image/png', data: await blankOut(picture, frame.masks.boxes)};
  frame.masks.applied = true;
  return {
    schema: SCHEMA,
    capture: {
      source: wasPasted(tab.url) ? 'pasted-url' : 'active-tab',
      url: storedAddress(tab.url),
      title: tab.title || frame.title,
      captured_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
      user_triggered: true,
    },
    frames: [frame],
  };
}

function render(reply, totalMs, picture) {
  if (!reply || reply.ok !== true) {
    show('problem', (reply && reply.message) || 'The local reviewer gave no result. Press the button again.');
    return;
  }
  const critique = reply.critique;
  drawRegion(picture, critique && critique.box).catch(() => { el('where').hidden = true; });
  el('finding').textContent = critique ? critique.problem : reply.message;
  el('change').textContent = critique ? critique.change : '';
  el('check').textContent = critique ? critique.outcome : '';
  el('fix').hidden = !critique;
  el('open').textContent = reply.has_after ? 'Open before and after' : 'Open the marked-up capture';
  el('open').dataset.url = reply.preview_url || '';
  el('path').textContent = reply.preview_path || '';
  el('result').hidden = false;
  el('scan').textContent = 'Scan again';
  const masked = reply.masked ? reply.masked.field + reply.masked.editable + reply.masked.frame : 0;
  const blanked = masked ? ' ' + masked + ' fields or frames blanked out.' : '';
  const more = reply.more_findings ? ' ' + reply.more_findings + ' more in the preview file.' : '';
  show('result', 'Scanned in ' + Math.round(totalMs) + ' ms. ' + reply.regions + ' regions measured.' + blanked + more + ' Nothing was uploaded.');
  el('open').focus();
}

async function scan() {
  const started = performance.now();
  el('scan').disabled = true;
  el('result').hidden = true;
  show('busy', 'Reading what is visible on this page…');
  try {
    const bundle = await capture();
    bundle.timings_ms = {capture: Math.round(performance.now() - started)};
    show('busy', 'Checking the page on this computer…');
    let reply;
    try {
      reply = await chrome.runtime.sendNativeMessage(HOST, {type: 'review', bundle});
    } catch (error) {
      throw hostProblem(error);
    }
    const total = performance.now() - started;
    remember('scan', total);
    render(reply, total, bundle.frames[0].screenshot.data);
  } catch (error) {
    if (error && error.shown) {
      show('problem', error.message, error.command);
    } else {
      console.error(error);
      show('problem', 'Something went wrong during the scan, and nothing was saved. Press the button again.');
    }
  } finally {
    el('scan').disabled = false;
    if (document.body.dataset.state === 'problem') el('scan').focus();
  }
}

function openPasted(event) {
  event.preventDefault();
  const typed = el('url').value.trim();
  const hasScheme = /^[a-z][a-z0-9+.-]*:\/\//i.test(typed) ||
    /^(about|blob|chrome|data|file|javascript|mailto|view-source):/i.test(typed);
  let target = null;
  try {
    target = new URL(hasScheme ? typed : 'https://' + typed);
  } catch (error) {
    target = null;
  }
  const host = target ? target.hostname : '';
  const local = host === 'localhost' || host.startsWith('[') || !host.includes('.') ||
    /\.(localhost|local|internal|lan)$/.test(host) ||
    /^(0|10|127)\.|^169\.254\.|^192\.168\.|^172\.(1[6-9]|2\d|3[01])\./.test(host);
  if (!typed || !target || !/^https?:$/.test(target.protocol) || target.username || target.password || local) {
    el('url-hint').textContent = 'Only public http and https pages can be opened from here. For any other page, open it yourself and press “Review this page” on it.';
    el('url').focus();
    return;
  }
  try {
    localStorage.setItem('dm.pasted', target.origin + target.pathname);
  } catch (error) { /* the source label is optional */ }
  chrome.tabs.create({url: target.href});
}

el('scan').addEventListener('click', scan);
el('open-form').addEventListener('submit', openPasted);
el('open').addEventListener('click', () => {
  const url = el('open').dataset.url || '';
  if (url.startsWith('file:///')) chrome.tabs.create({url});
});
show('idle', IDLE_TEXT);
