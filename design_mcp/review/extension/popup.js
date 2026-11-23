'use strict';

/* The popup does nothing until a button is pressed: no request, no page access, no message to the
   local reviewer. Pressing "Review this page" reads the visible part of the active tab, blanks out
   fields in the picture, and hands the capture to the local reviewer on this computer. */

const HOST = 'com.design_mcp.review';
const SCHEMA = 'design-mcp.page-evidence/1';
const IDLE_TEXT = 'Scans only what you can see in this tab. Form fields are blanked out. Nothing is uploaded.';
const el = id => document.getElementById(id);
const reviewTab = new URLSearchParams(location.search).get('view') === 'url';

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

// Show the affected part of the capture itself, outlined, with a little of the page around it.
async function drawRegion(base64, box) {
  const canvas = el('where');
  canvas.hidden = true;
  const thumbnail = base64?.startsWith('data:image/jpeg;base64,');
  if (!base64 || (!box && !thumbnail)) return;
  const image = new Image();
  image.src = thumbnail ? base64 : 'data:image/png;base64,' + base64;
  await image.decode();
  canvas.setAttribute('aria-label', box ? 'The part of the page this finding is about' : 'The page as captured');
  const area = box || {x: 0, y: 0, width: 1, height: 1};
  const pad = 0.04;
  const left = Math.max(0, area.x - pad);
  const top = Math.max(0, area.y - pad);
  const right = Math.min(1, area.x + area.width + pad);
  const bottom = Math.min(1, area.y + area.height + pad);
  const sw = (right - left) * image.naturalWidth;
  const sh = (bottom - top) * image.naturalHeight;
  const ratio = window.devicePixelRatio || 1;
  const cssWidth = reviewTab ? canvas.parentElement.clientWidth : 336;
  canvas.width = Math.round(cssWidth * ratio);
  canvas.height = Math.round(Math.max(48, Math.min(168, cssWidth * sh / sw)) * ratio);
  const fit = Math.min(canvas.width / sw, canvas.height / sh);
  const dx = (canvas.width - sw * fit) / 2;
  const dy = (canvas.height - sh * fit) / 2;
  const pen = canvas.getContext('2d');
  pen.fillStyle = '#ffffff';
  pen.fillRect(0, 0, canvas.width, canvas.height);
  pen.drawImage(image, left * image.naturalWidth, top * image.naturalHeight, sw, sh, dx, dy, sw * fit, sh * fit);
  if (box) {
    pen.lineWidth = 2 * ratio;
    pen.strokeStyle = '#b4235a';
    pen.strokeRect(
      dx + (box.x - left) * image.naturalWidth * fit, dy + (box.y - top) * image.naturalHeight * fit,
      box.width * image.naturalWidth * fit, box.height * image.naturalHeight * fit);
  }
  canvas.hidden = false;
}

function storedAddress(url) {
  const address = new URL(url);
  address.hash = '';
  address.username = '';
  address.password = '';
  return address.href;
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
      target: {tabId: tab.id}, func: designMcpCollect, args: [{maxRegions: 8}],
    });
  } catch (error) {
    throw problem('Chrome did not allow a picture of this tab, so nothing was saved. Press the button again.');
  }
  const [still] = await chrome.tabs.query({active: true, currentWindow: true});
  const after = probe?.result;
  // A field can move or appear without changing the tab, viewport, or scroll position.
  const geometry = value => JSON.stringify([value.document, value.viewport, value.masks?.boxes]);
  if (!still || still.id !== tab.id || still.url !== tab.url || !after ||
      geometry(after) !== geometry(frame)) {
    throw problem('The page moved or the tab changed during the scan, so nothing was saved. Leave the page still for a second and press the button again.');
  }

  frame.screenshot = {media_type: 'image/png', data: await maskPagePicture(picture, frame.masks.boxes)};
  frame.masks.applied = true;
  return {
    schema: SCHEMA,
    capture: {
      source: 'active-tab',
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
  drawRegion(picture || reply.thumbnail, critique && critique.box).catch(() => { el('where').hidden = true; });
  el('finding').textContent = critique ? critique.problem : reply.message;
  el('change').textContent = critique ? critique.change : '';
  el('check').textContent = critique ? critique.outcome : '';
  el('fix').hidden = !critique;
  el('open').textContent = reply.has_after ? 'Open before and after' : critique ? 'Open the marked-up capture' : 'Open the capture';
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

async function reviewAddress(url) {
  const started = performance.now();
  el('review-url').disabled = true;
  el('result').hidden = true;
  show('busy', 'Opening the page in a separate Chrome session…');
  try {
    const reply = await chrome.runtime.sendNativeMessage(HOST, {type: 'review-url', url});
    if (reply?.code === 'unknown-request') {
      throw problem('Update Design MCP and reconnect the local reviewer, then try this address again.',
        'design-mcp review --install-host ' + chrome.runtime.id);
    }
    render(reply, performance.now() - started);
  } catch (error) {
    const failure = error?.shown ? error : hostProblem(error);
    show('problem', failure.message, failure.command);
  } finally {
    el('review-url').disabled = false;
    if (document.body.dataset.state === 'problem') el('url').focus();
  }
}

async function openPasted(event) {
  event.preventDefault();
  if (el('review-url').disabled) return;
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
    el('url-hint').textContent = 'Enter a public web address. For a private page you already have open, use “Review this page”.';
    el('url').focus();
    return;
  }
  el('url-hint').textContent = '';
  if (reviewTab) {
    await reviewAddress(target.href);
    return;
  }
  el('review-url').disabled = true;
  const key = crypto.randomUUID();
  try {
    await chrome.storage.session.set({[key]: target.href});
    await chrome.tabs.create({url: chrome.runtime.getURL('popup.html?view=url#' + key)});
  } catch (error) {
    await chrome.storage.session.remove(key).catch(() => {});
    el('url-hint').textContent = 'Chrome could not open the review. Try again.';
    el('review-url').disabled = false;
    el('url').focus();
  }
}

async function startReviewTab() {
  document.body.dataset.view = 'url';
  el('scan').removeAttribute('autofocus');
  el('title').textContent = 'Review a public page';
  el('url-hint').textContent = 'Fields are blanked out before the capture is saved.';
  show('idle', 'Paste an address to check layout and contrast.');
  const key = location.hash.slice(1);
  if (!/^[0-9a-f-]{36}$/.test(key)) return;
  history.replaceState(null, '', location.pathname + location.search);
  try {
    const { [key]: url } = await chrome.storage.session.get(key);
    await chrome.storage.session.remove(key);
    if (typeof url !== 'string') throw new Error('Review request missing');
    // Leave the address editable for retry without retaining it in browser history.
    el('url').value = url;
    await reviewAddress(url);
  } catch (error) {
    show('problem', 'The address did not reach the reviewer. Paste it here and try again.');
    el('url').focus();
  }
}

el('scan').addEventListener('click', scan);
el('open-form').addEventListener('submit', openPasted);
el('open').addEventListener('click', () => {
  const url = el('open').dataset.url || '';
  if (url.startsWith('file:///')) chrome.tabs.create({url});
});
show('idle', IDLE_TEXT);
if (reviewTab) startReviewTab();
