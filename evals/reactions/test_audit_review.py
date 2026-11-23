import base64
from io import BytesIO
import random
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


def test_lossless_bands_verify_order_and_pixels(tmp_path, monkeypatch):
    image_module = pytest.importorskip("PIL.Image")
    import live_browser

    width, height = 390, 844
    raster = image_module.frombytes("RGB", (width, height), random.Random(11).randbytes(width * height * 3))
    buf = BytesIO()
    raster.save(buf, format="PNG")
    original = buf.getvalue()
    assert live_browser.original_image(original) is None
    bands = live_browser.original_bands(original)
    assert [(top, bottom) for top, bottom, _ in bands] == [(0, 422), (422, 844)]
    assert all(len(payload) <= live_browser.MAX_ORIGINAL_PNG_BYTES for _, _, payload in bands)

    label = "A-390-before"
    path = tmp_path / "captures" / f"{label}.png"
    path.parent.mkdir()
    path.write_bytes(original)
    receipt_bands = [{"top": top, "bottom": bottom, "sha256": sha256(payload)} for top, bottom, payload in bands]
    row = {"page_id": "A", "path": path.name, "observation": {"width": width}, "sha256": sha256(original),
           "transport": {"mime_type": "image/webp", "bands": receipt_bands}}
    images = [live_browser.image_block("image/webp", payload).model_dump(by_alias=True) for _, _, payload in bands]
    calls = [
        {"id": "photo", "tool": "capture", "arguments": {"label": label}, "result": {"content": images[:1]}},
        {"id": "bottom", "tool": "capture", "arguments": {"label": label, "band": "bottom"},
         "result": {"content": images[1:]}},
    ]
    index, verified = screenshot(tmp_path, "A", width, "before", {label: (1, row)}, calls)
    assert index == 1 and verified["transport"] == row["transport"]

    # Even a replacement digest cannot certify pixels from the wrong band.
    calls[0]["result"]["content"], calls[1]["result"]["content"] = images[1:], images[:1]
    receipt_bands[0]["sha256"] = sha256(bands[1][2])
    with pytest.raises(AssertionError, match=label):
        screenshot(tmp_path, "A", width, "before", {label: (1, row)}, calls)
    monkeypatch.setattr(live_browser, "MAX_ORIGINAL_PNG_BYTES", 100)
    assert live_browser.original_bands(original) is None


def test_arrow_key_counts_only_when_it_changes_the_checked_radio():
    def action(key, name, ax):
        return {"action": "key", "value": key, "observation": {"focus": {"label": name}, "ax": ax}}

    before = action("Tab", "4 m", '- radio "4 m" [checked]\n- radio "6 m"')
    after = action("ArrowRight", "6 m", '- radio "4 m"\n- radio "6 m" [checked]')
    assert keyboard_activation([before, after], allow_radio=True)
    assert not keyboard_activation([before, after])
    unrelated = action("ArrowRight", "6 m", '- radio "4 m" [checked]\n- radio "6 m"')
    assert not keyboard_activation([before, unrelated], allow_radio=True)


def test_radio_audit_uses_the_accessible_name_when_visible_label_is_abbreviated():
    before = {
        "action": "key", "value": "Tab",
        "observation": {
            "focus": {"label": "Tue", "radio": '- radio "Tuesday" [checked]'},
            "ax": '- radio "Tuesday" [checked]\n- radio "Wednesday"',
        },
    }
    after = {
        "action": "key", "value": "ArrowRight",
        "observation": {
            "focus": {"label": "Wed", "radio": '- radio "Wednesday" [checked]'},
            "ax": '- radio "Tuesday"\n- radio "Wednesday" [checked]',
        },
    }
    assert keyboard_activation([before, after], allow_radio=True)
    after["observation"]["focus"]["radio"] = '- button "Wednesday"'
    assert not keyboard_activation([before, after], allow_radio=True)
