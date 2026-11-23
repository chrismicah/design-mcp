"""Seal the original and font-loading-only variants of two exact browser fixtures."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parent
archive = root.parent / "practice_call_board/cells"
destination = Path(sys.argv[1])
sources = {
    "tacoma-eye-care": "reaction-control",
    "dayton-physiotherapy": "focus-editable-note",
}
pattern = rb'(<link(?=[^>]+\brel="stylesheet")(?=[^>]+\bhref="https://fonts\.googleapis\.com/)[^>]+)>'
for case, arm in sources.items():
    path = archive / case / arm
    original = (path / "index.html").read_bytes()
    parent = sha256(original).hexdigest()
    assert json.loads((path / "receipt.json").read_bytes())["html_sha256"] == parent
    link, = list(re.finditer(pattern, original))
    deferred = (link[1] + b' media="print" onload="this.media=\'all\'">' +
                b'\n  <noscript>' + link[0] + b'</noscript>')
    for label, page in (("blocking", original), ("deferred", original.replace(link[0], deferred, 1))):
        target = destination / case / label
        target.mkdir(parents=True)
        (target / "index.html").write_bytes(page)
        (target / "receipt.json").write_text(json.dumps({
            "case": case, "label": label, "parent_html_sha256": parent,
            "html_sha256": sha256(page).hexdigest(),
        }, indent=2) + "\n")
