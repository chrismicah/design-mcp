import base64
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


def test_arrow_key_counts_only_when_it_changes_the_checked_radio():
    def action(key, name, ax):
        return {"action": "key", "value": key, "observation": {"focus": {"label": name}, "ax": ax}}

    before = action("Tab", "4 m", '- radio "4 m" [checked]\n- radio "6 m"')
    after = action("ArrowRight", "6 m", '- radio "4 m"\n- radio "6 m" [checked]')
    assert keyboard_activation([before, after], allow_radio=True)
    assert not keyboard_activation([before, after])
    unrelated = action("ArrowRight", "6 m", '- radio "4 m" [checked]\n- radio "6 m"')
    assert not keyboard_activation([before, unrelated], allow_radio=True)
