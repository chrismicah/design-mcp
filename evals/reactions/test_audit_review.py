import base64
from io import BytesIO
import struct

import pytest

from audit_review import keyboard_activation, screenshot, sha256


def test_capture_must_be_the_same_png_sent_to_the_critic(tmp_path):
    prefix = b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + struct.pack(">II", 390, 844)
    original = prefix + b"original pixels"
    label = "A-390-before"
    filename = f"{label}.png"
    (tmp_path / "captures").mkdir()
    (tmp_path / "captures" / filename).write_bytes(original)
    indexed = {
        label: (
            1,
            {"page_id": "A", "path": filename, "observation": {"width": 390},
             "sha256": sha256(original)},
        )
    }
    image = {"type": "image", "mimeType": "image/png", "data": base64.b64encode(original).decode()}
    call = {
        "id": "photo",
        "tool": "capture",
        "arguments": {"label": label},
        "result": {"content": [image]},
    }
    index, verified = screenshot(tmp_path, "A", 390, "before", indexed, [call])
    assert index == 1 and verified["sha256"] == sha256(original)

    image["data"] = base64.b64encode(prefix + b"other pixels").decode()
    with pytest.raises(AssertionError, match=label):
        screenshot(tmp_path, "A", 390, "before", indexed, [call])


def test_large_capture_can_use_lossless_pixel_verified_webp(tmp_path, monkeypatch):
    image_module = pytest.importorskip("PIL.Image")
    import live_browser

    raster = image_module.new("RGBA", (390, 844), (52, 56, 61, 255))
    raster.putpixel((0, 0), (17, 19, 21, 0))
    buf = BytesIO()
    raster.save(buf, format="PNG", compress_level=0)
    original = buf.getvalue()
    assert len(original) > live_browser.MAX_ORIGINAL_PNG_BYTES
    mime, encoded = live_browser.original_image(original)
    assert mime == "image/webp" and len(encoded) <= live_browser.MAX_ORIGINAL_PNG_BYTES
    label = "A-390-before"
    filename = f"{label}.png"
    (tmp_path / "captures").mkdir()
    (tmp_path / "captures" / filename).write_bytes(original)
    row = {"page_id": "A", "path": filename, "observation": {"width": 390}, "sha256": sha256(original)}
    image = {"type": "image", "mimeType": mime}
    calls = [{"id": "photo", "tool": "capture", "arguments": {"label": label}, "result": {"content": [image]}}]
    row["transport"] = {"mime_type": mime, "sha256": sha256(encoded)}
    image["data"] = base64.b64encode(encoded).decode()
    index, verified = screenshot(tmp_path, "A", 390, "before", {label: (1, row)}, calls)
    assert index == 1 and verified["transport"] == row["transport"]

    raster.putpixel((385, 840), (60, 60, 61, 255))
    changed = BytesIO()
    raster.save(changed, format="WEBP", lossless=True, exact=True)
    row["transport"]["sha256"] = sha256(changed.getvalue())
    image["data"] = base64.b64encode(changed.getvalue()).decode()
    with pytest.raises(AssertionError, match=label):
        screenshot(tmp_path, "A", 390, "before", {label: (1, row)}, calls)

    monkeypatch.setattr(live_browser, "MAX_ORIGINAL_PNG_BYTES", 32)
    assert live_browser.original_image(original) is None


def test_arrow_key_counts_only_when_it_changes_the_checked_radio():
    def action(key, name, ax):
        return {"action": "key", "value": key, "observation": {"focus": {"label": name}, "ax": ax}}

    before = action("Tab", "4 m", '- radio "4 m" [checked]\n- radio "6 m"')
    after = action("ArrowRight", "6 m", '- radio "4 m"\n- radio "6 m" [checked]')
    assert keyboard_activation([before, after], allow_radio=True)
    assert not keyboard_activation([before, after])
    unrelated = action("ArrowRight", "6 m", '- radio "4 m" [checked]\n- radio "6 m"')
    assert not keyboard_activation([before, unrelated], allow_radio=True)
