() => {
  const candidates = document.querySelectorAll('h1, h2, button, [role="button"], nav a, main a, figure img, main img, [role="img"], label, [role="status"]');
  const regions = [];
  for (const element of candidates) {
    const rect = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    if (style.visibility !== 'visible' || style.opacity === '0' || rect.width < 1 || rect.height < 1 ||
        rect.bottom <= 0 || rect.top >= innerHeight || rect.right <= 0 || rect.left >= innerWidth) continue;
    if (element.closest('input, textarea, [contenteditable], [hidden], [aria-hidden="true"]')) continue;
    const label = (element.getAttribute('aria-label') || element.getAttribute('alt') ||
      element.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 56);
    regions.push({
      role: element.getAttribute('role') || element.tagName.toLowerCase(),
      label,
      box: [rect.x, rect.y, rect.width, rect.height].map(Math.round),
      type: [style.fontSize, style.fontWeight, style.fontFamily.split(',')[0]],
      ink: style.color,
      fill: style.backgroundColor,
      ...(element.hasAttribute('aria-pressed') ? {pressed: element.getAttribute('aria-pressed')} : {}),
    });
    if (regions.length >= 12) break;
  }
  return regions;
}
