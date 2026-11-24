"""Locate the test extension's icon in a screenshot of the isolated desktop."""

import sys

from PIL import Image


def locate(image, width):
    toolbar = image.convert("RGB").crop((0, 0, min(width, image.width), 140))
    matches = []
    for y in range(toolbar.height):
        for x in range(toolbar.width):
            red, green, blue = toolbar.getpixel((x, y))
            if red >= 205 and green <= 45 and 120 <= blue <= 225:
                matches.append((x, y))
    if not matches:
        return None
    left, right = min(x for x, _ in matches), max(x for x, _ in matches)
    top, bottom = min(y for _, y in matches), max(y for _, y in matches)
    if not 5 <= right - left <= 20 or not 5 <= bottom - top <= 20:
        raise ValueError("More than one marker or an unexpected marker size")
    return (left + right) // 2, (top + bottom) // 2


if __name__ == "__main__":
    with Image.open(sys.argv[1]) as image:
        marker = locate(image, int(sys.argv[2]))
    if marker:
        print(*marker)
