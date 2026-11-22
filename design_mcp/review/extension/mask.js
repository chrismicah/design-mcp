/* Paint over private areas before saving or forwarding the picture. */
async function maskPagePicture(dataUrl, boxes) {
  if (!boxes.length) return dataUrl.slice(dataUrl.indexOf(',') + 1);
  const image = new Image();
  image.src = dataUrl;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const pen = canvas.getContext('2d');
  pen.drawImage(image, 0, 0);
  pen.fillStyle = '#8a8f98';
  for (const item of boxes) {
    pen.fillRect(
      Math.floor(item.box.x * canvas.width) - 1, Math.floor(item.box.y * canvas.height) - 1,
      Math.ceil(item.box.width * canvas.width) + 2, Math.ceil(item.box.height * canvas.height) + 2);
  }
  const masked = canvas.toDataURL('image/png');
  return masked.slice(masked.indexOf(',') + 1);
}

async function reviewThumbnail(dataUrl) {
  const image = new Image();
  image.src = dataUrl;
  await image.decode();
  const canvas = document.createElement('canvas');
  canvas.width = Math.min(640, image.naturalWidth);
  canvas.height = Math.round(image.naturalHeight * canvas.width / image.naturalWidth);
  canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
  const thumbnail = canvas.toDataURL('image/jpeg', 0.72);
  return thumbnail.length <= 192 * 1024 ? thumbnail : null;
}
