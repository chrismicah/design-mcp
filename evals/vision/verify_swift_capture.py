"""Verify the exact XCUI exports using an installed Design MCP executable."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(attachments, executable, proof):
    manifest = json.loads((attachments / "manifest.json").read_bytes())
    attachments_by_name = [
        (entry["suggestedHumanReadableName"], attachments / entry["exportedFileName"])
        for test in manifest for entry in test["attachments"]
        if not entry["isAssociatedWithFailure"]
    ]
    proof.mkdir()
    reviewed = {}
    for state in ("before", "after"):
        exports = {}
        for kind, prefix, suffix in (
            ("geometry", "design-capture", "json"), ("pixels", "window-pixels", "png")
        ):
            candidates = [path for name, path in attachments_by_name if f"{prefix}-{state}" in name]
            assert len(candidates) == 1, (state, kind, [name for name, _ in attachments_by_name])
            destination = proof / f"{state}.{suffix}"
            shutil.copyfile(candidates[0], destination)
            exports[kind] = destination
        pixels = exports["pixels"].read_bytes()
        assert pixels.startswith(b"\x89PNG\r\n\x1a\n") and len(pixels) > 1000
        data = exports["geometry"].read_bytes()
        capture = json.loads(data)
        assert b"swift-review-fixture-private-marker" not in data
        reviewed[state] = {
            "geometry_sha256": digest(exports["geometry"]),
            "pixels_sha256": digest(exports["pixels"]),
            "buttons": sum(region["role"] == "button" and region["hittable"] for region in capture["regions"]),
            "result": json.loads(subprocess.check_output([str(executable), "review-app", str(exports["geometry"])])),
        }
        assert reviewed[state]["result"]["platform"] == "swift"
    before, after = reviewed["before"], reviewed["after"]
    assert before["result"]["viewport"] == after["result"]["viewport"]
    assert before["buttons"] >= 1 and after["buttons"] == before["buttons"] + 1, reviewed
    assert before["result"]["controls_reviewed"] + 1 == after["result"]["controls_reviewed"], reviewed
    assert before["pixels_sha256"] != after["pixels_sha256"]
    (proof / "receipt.json").write_text(json.dumps(reviewed, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reviewed, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attachments", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("proof", type=Path)
    args = parser.parse_args()
    main(args.attachments, args.executable, args.proof)
