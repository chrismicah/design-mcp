/* Center a known master-image point in a compatible absolute image crop.
 * The caller owns the image, clip, and source metadata. The returned placement
 * can be applied as CSS pixels after decoding the image and opening the clip.
 */
function centerImageFocus({frameWidth, frameHeight, imageWidth, imageHeight, x, y, magnification=2}) {
  if (![frameWidth,frameHeight,imageWidth,imageHeight,x,y,magnification].every(Number.isFinite) ||
      Math.min(frameWidth,frameHeight,imageWidth,imageHeight) <= 0 ||
      x < 0 || x > 1 || y < 0 || y > 1 || magnification <= 1 || magnification > 8) {
    throw new RangeError("Expected positive dimensions, a normalized point and magnification above 1 through 8.");
  }
  const scale = magnification * Math.max(frameWidth/imageWidth,frameHeight/imageHeight);
  const width = imageWidth*scale;
  const height = imageHeight*scale;
  return {
    width,height,
    left:Math.max(frameWidth-width,Math.min(0,frameWidth/2-x*width)),
    top:Math.max(frameHeight-height,Math.min(0,frameHeight/2-y*height)),
  };
}
