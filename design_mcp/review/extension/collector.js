/* Runs inside the page being reviewed and reports what is visible: boxes, type, colors and names.
   It is one self-contained function, so the extension can inject it with chrome.scripting.executeScript
   and the separate-browser capture can evaluate the same source. It changes nothing on the page and
   never reads what someone typed into a field. */
function designMcpCollect(options) {
  const maxRegions = (options && options.maxRegions) || 8;
  const walkLimit = (options && options.walkLimit) || 20000;
  const candidateLimit = (options && options.candidateLimit) || 400;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const root = document.documentElement;
  const clientWidth = root.clientWidth;
  const pageOverflows = root.scrollWidth - clientWidth > 1;

  const short = (text, limit) => String(text || '').replace(/\s+/g, ' ').trim().slice(0, limit || 80);
  const round4 = value => Math.round(value * 10000) / 10000;
  const boxOf = rect => ({
    x: round4(rect.left / vw), y: round4(rect.top / vh),
    width: round4(rect.width / vw), height: round4(rect.height / vh),
  });

  // Colors as [red, green, blue, alpha]. Common rgb() text is read directly; anything else goes through a canvas.
  const legacy = /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:\s*[,/]\s*([\d.]+%?))?\s*\)$/;
  const colors = new Map();
  let pen = null;
  const rgba = value => {
    if (colors.has(value)) return colors.get(value);
    let out = null;
    const match = legacy.exec(value);
    if (match) {
      let alpha = match[4] === undefined ? 1 : parseFloat(match[4]);
      if (match[4] && match[4].endsWith('%')) alpha /= 100;
      out = [Math.round(Number(match[1])), Math.round(Number(match[2])), Math.round(Number(match[3])), alpha];
    } else {
      try {
        if (!pen) {
          const canvas = document.createElement('canvas');
          canvas.width = canvas.height = 1;
          pen = canvas.getContext('2d', {willReadFrequently: true});
        }
        pen.clearRect(0, 0, 1, 1);
        pen.fillStyle = '#010203';
        pen.fillStyle = value;
        pen.fillRect(0, 0, 1, 1);
        const data = pen.getImageData(0, 0, 1, 1).data;
        const sentinel = data[0] === 1 && data[1] === 2 && data[2] === 3 && data[3] === 255;
        out = sentinel ? null : [data[0], data[1], data[2], Math.round(data[3] / 255 * 1000) / 1000];
      } catch (error) {
        out = null;
      }
    }
    colors.set(value, out);
    return out;
  };

  const shown = el => {
    if (typeof el.checkVisibility === 'function') {
      return el.checkVisibility({
        checkOpacity: true, checkVisibilityCSS: true, opacityProperty: true, visibilityProperty: true,
      });
    }
    const style = getComputedStyle(el);
    return style.display !== 'none' && style.visibility === 'visible' && Number(style.opacity) > 0;
  };
  const inView = rect => rect.bottom > 0 && rect.top < vh && rect.right > 0 && rect.left < vw;

  const buttonTypes = /^(button|submit|reset|image)$/;
  const isField = el => el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' ||
    (el.tagName === 'INPUT' && !buttonTypes.test(el.type) && el.type !== 'hidden');
  const isEditableHost = el => el.isContentEditable === true &&
    !(el.parentElement && el.parentElement.isContentEditable === true);
  const isFrame = el => /^(IFRAME|FRAME|EMBED|OBJECT)$/.test(el.tagName);

  // Text a person can read on the page, leaving out anything typed, selected or editable.
  const blocked = 'textarea, select, option, script, style, noscript, template';
  const safeText = el => {
    if (!el || el.isContentEditable === true || el.closest(blocked)) return '';
    const texts = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let out = '';
    while (out.length < 240 && texts.nextNode()) {
      const parent = texts.currentNode.parentElement;
      if (!parent || parent.isContentEditable === true || parent.closest(blocked)) continue;
      out += texts.currentNode.nodeValue + ' ';
    }
    return out;
  };
  const ownText = el => {
    for (const node of el.childNodes) if (node.nodeType === 3 && node.nodeValue.trim()) return true;
    return false;
  };

  const nameOf = el => {
    const ids = el.getAttribute('aria-labelledby');
    if (ids) {
      const text = short(ids.split(/\s+/).map(id => safeText(document.getElementById(id))).join(' '));
      if (text) return text;
    }
    const aria = short(el.getAttribute('aria-label'));
    if (aria) return aria;
    if (isField(el)) {
      const label = el.labels && el.labels[0];
      return short(label ? safeText(label) : el.getAttribute('placeholder') || el.getAttribute('title'));
    }
    if (el.tagName === 'INPUT') return short(el.getAttribute('value') || el.getAttribute('alt') || el.type);
    if (el.tagName === 'IMG') return short(el.getAttribute('alt'));
    return short(safeText(el)) || short(el.getAttribute('title'));
  };
  const labelOf = el => short(el.getAttribute('aria-label')) || short(el.getAttribute('alt')) ||
    short(safeText(el.querySelector('caption, legend, h1, h2, h3, h4, [role="heading"]')));

  const roleOf = el => {
    const explicit = short(el.getAttribute('role'), 24);
    if (explicit) return explicit;
    const tag = el.tagName.toLowerCase();
    if (/^h[1-6]$/.test(tag)) return 'heading';
    if (tag === 'a') return 'link';
    if (tag === 'button' || (tag === 'input' && buttonTypes.test(el.type))) return 'button';
    if (tag === 'img') return 'img';
    if (tag === 'select') return 'combobox';
    if (tag === 'textarea' || tag === 'input') return 'field';
    return 'text';
  };

  const landmarks = 'main, nav, header, footer, aside, form, dialog, [role="main"], [role="navigation"], ' +
    '[role="banner"], [role="contentinfo"], [role="complementary"], [role="search"], [role="form"], ' +
    '[role="region"], [role="dialog"]';
  const landmarkOf = el => {
    const node = el.closest(landmarks);
    return node ? short(node.getAttribute('role') || node.tagName.toLowerCase(), 24) : '';
  };

  const locatorOf = el => {
    const parts = [];
    for (let node = el; node && node.nodeType === 1 && node !== root && parts.length < 4; node = node.parentElement) {
      const id = node.getAttribute('id');
      if (id && /^[A-Za-z][\w-]{0,31}$/.test(id) && !/\d{4,}/.test(id)) {
        parts.unshift('#' + id);
        break;
      }
      const tag = node.tagName.toLowerCase();
      const same = node.parentElement
        ? Array.prototype.filter.call(node.parentElement.children, child => child.tagName === node.tagName)
        : [node];
      parts.unshift(same.length > 1 ? tag + ':nth-of-type(' + (same.indexOf(node) + 1) + ')' : tag);
    }
    return parts.join(' > ');
  };

  // The fill behind a piece of text, found by looking at what is painted under its center point.
  // It only counts as flat when the first paint underneath is one opaque color.
  const lightCanvas = !/dark/.test(getComputedStyle(root).colorScheme || '');
  const replaced = /^(img|video|canvas|svg|picture|iframe|object|embed)$/i;
  const unknownFill = {fill: null, flat: false};
  const fillAt = (el, rect) => {
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;
    if (x < 0 || y < 0 || x >= vw || y >= vh) return unknownFill;
    let reached = false;
    for (const node of document.elementsFromPoint(x, y)) {
      const own = node === el || el.contains(node);
      if (own) reached = true;
      if (!reached && !node.contains(el)) return unknownFill;
      if (!own && replaced.test(node.tagName)) return unknownFill;
      const style = getComputedStyle(node);
      if (style.backgroundImage !== 'none' || Number(style.opacity) < 1 || style.mixBlendMode !== 'normal') {
        return unknownFill;
      }
      const color = rgba(style.backgroundColor);
      if (!color) return unknownFill;
      if (color[3] >= 1) return {fill: color, flat: true};
      if (color[3] > 0) return unknownFill;
    }
    return lightCanvas ? {fill: [255, 255, 255, 1], flat: true} : unknownFill;
  };

  const found = [];
  const masks = [];
  let widest = null;
  let heading = '';
  let order = 0;
  let walked = 0;
  const elements = document.createTreeWalker(document.body || root, NodeFilter.SHOW_ELEMENT);
  for (let el = elements.nextNode(); el && walked < walkLimit; el = elements.nextNode()) {
    walked += 1;
    const tag = el.tagName.toLowerCase();
    if (/^(script|style|noscript|template|br|wbr|option|optgroup)$/.test(tag)) continue;
    const rect = el.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1 || !shown(el)) continue;
    const isHeading = /^h[1-6]$/.test(tag) || el.getAttribute('role') === 'heading';
    if (pageOverflows) {
      // Keep the innermost element that reaches the far right edge: later in the page means deeper.
      const right = rect.right + window.scrollX;
      if (right > clientWidth + 1 && (!widest || right >= widest.max - 1)) {
        widest = {el, max: Math.max(right, widest ? widest.max : 0)};
      }
    }
    if (!inView(rect)) {
      if (isHeading) heading = short(safeText(el)) || heading;
      continue;
    }
    const field = isField(el);
    const editable = isEditableHost(el);
    const frame = isFrame(el);
    if (field || editable || frame) {
      masks.push({kind: frame ? 'frame' : field ? 'field' : 'editable', box: boxOf(rect)});
    }
    if (frame || el.isContentEditable === true) continue;

    const role = el.getAttribute('role');
    const control = tag === 'button' || role === 'button' || (tag === 'input' && buttonTypes.test(el.type));
    const link = tag === 'a' && el.hasAttribute('href');
    const status = role === 'status' || role === 'alert' || el.hasAttribute('aria-live');
    const image = tag === 'img' || role === 'img';
    const text = !field && ownText(el);
    if (!(control || link || isHeading || status || image || field || text) || found.length >= candidateLimit) {
      if (isHeading) heading = short(safeText(el)) || heading;
      continue;
    }
    const style = getComputedStyle(el);
    const paint = text ? fillAt(el, rect) : unknownFill;
    order += 1;
    found.push({
      el, rect, control, link, status, isHeading,
      level: /^h[1-6]$/.test(tag) ? Number(tag[1]) : 0,
      region: {
        role: roleOf(el),
        name: nameOf(el),
        landmark: landmarkOf(el),
        heading: isHeading ? '' : heading,
        locator: locatorOf(el),
        reading_order: order,
        box: boxOf(rect),
        font: {
          family: short(style.fontFamily.split(',')[0].replace(/["']/g, ''), 60),
          size_px: parseFloat(style.fontSize),
          weight: Number(style.fontWeight) || 400,
        },
        ink: text ? rgba(style.color) : null,
        fill: paint.fill,
        fill_flat: paint.flat,
        has_text: text,
        masked: field,
        disabled: el.disabled === true || el.getAttribute('aria-disabled') === 'true',
        pressed: el.getAttribute('aria-pressed'),
      },
    });
    if (isHeading) heading = short(safeText(el)) || heading;
  }

  // The main button: the first enabled button, preferring one inside the main content or a form.
  const inContent = record => record.el.closest('main, [role="main"], form') !== null;
  const buttons = found.filter(record => record.control && !record.region.disabled);
  const inMain = buttons.find(inContent);
  const primary = inMain || buttons[0] || null;
  let cover = null;
  if (primary) {
    const x = primary.rect.left + primary.rect.width / 2;
    const y = primary.rect.top + primary.rect.height / 2;
    const top = x >= 0 && y >= 0 && x < vw && y < vh ? document.elementFromPoint(x, y) : null;
    if (top && top !== primary.el && !primary.el.contains(top) && !top.contains(primary.el)) {
      for (let node = top; node && node.nodeType === 1; node = node.parentElement) {
        const position = getComputedStyle(node).position;
        if (position !== 'fixed' && position !== 'sticky') continue;
        if (!node.contains(primary.el)) {
          const bar = node.getBoundingClientRect();
          cover = {
            position, name: labelOf(node), locator: locatorOf(node),
            box: boxOf(bar), height_px: Math.round(bar.height),
          };
        }
        break;
      }
    }
  }

  // Which regions to report: structure first, then the hardest text to read, then the rest in reading order.
  const linear = channel => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
  };
  const luminance = color => 0.2126 * linear(color[0]) + 0.7152 * linear(color[1]) + 0.0722 * linear(color[2]);
  const contrast = record => {
    const region = record.region;
    if (!region.has_text || region.disabled || region.fill_flat !== true || !region.ink || !region.fill) return 99;
    if (region.font.size_px >= 24 || (region.font.size_px >= 18.66 && region.font.weight >= 700)) return 99;
    const alpha = region.ink[3];
    const ink = [0, 1, 2].map(index => alpha * region.ink[index] + (1 - alpha) * region.fill[index]);
    const a = luminance(ink);
    const b = luminance(region.fill);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };
  const chosen = [];
  const take = record => {
    if (record && chosen.length < maxRegions && chosen.indexOf(record) < 0) chosen.push(record);
  };
  take(found.find(record => record.level === 1) || found.find(record => record.isHeading));
  take(primary);
  take(found.find(record => inContent(record) && record.region.masked && record.region.name));
  found.map(record => ({record, ratio: contrast(record)})).filter(item => item.ratio < 4.5)
    .sort((a, b) => a.ratio - b.ratio).slice(0, 3).forEach(item => take(item.record));
  take(found.find(record => record.status && inContent(record)) || found.find(record => record.status));
  found.filter(record => inContent(record) && (record.isHeading || record.control || record.region.masked)).forEach(take);
  found.filter(record => record.isHeading || record.control || record.status).forEach(take);
  found.forEach(take);
  chosen.sort((a, b) => a.region.reading_order - b.region.reading_order);
  chosen.forEach((record, index) => { record.region.id = 'r' + (index + 1); });

  return {
    viewport: {width: vw, height: vh, dpr: window.devicePixelRatio || 1},
    document: {
      scroll_width: root.scrollWidth, client_width: clientWidth, lang: short(root.getAttribute('lang'), 16),
      scroll_x: Math.round(window.scrollX), scroll_y: Math.round(window.scrollY),
    },
    title: short(document.title, 120),
    regions: chosen.map(record => record.region),
    overflow: widest
      ? {name: labelOf(widest.el), locator: locatorOf(widest.el), box: boxOf(widest.el.getBoundingClientRect())}
      : null,
    primary_control: primary && chosen.indexOf(primary) >= 0
      ? {
        region: primary.region.id,
        basis: inMain ? 'first button inside the main content' : 'first button on the page',
        covered_by: cover,
      }
      : null,
    masks: {applied: false, boxes: masks},
  };
}
