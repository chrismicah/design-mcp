"""Validate the reviewed reference sample and print eligible builder inputs."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
from urllib.parse import urlsplit


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GROUPS = {"utility", "expressive", "quiet"}
STATES = {"found", "rendered-only", "incomplete", "interaction-verified"}
PACKET = ("transfer", "prediction", "falsifier")


def required(row, fields):
    for field in fields:
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"{row.get('name', 'Unknown reference')}: missing {field}")


def capture_path(frame):
    required(frame, ("path", "sha256"))
    viewport = frame.get("viewport")
    if not isinstance(viewport, list) or len(viewport) != 2 or any(
        type(dimension) is not int or dimension <= 0 for dimension in viewport
    ):
        raise ValueError(f"Invalid CSS viewport: {frame['path']}")
    if not re.fullmatch("[0-9a-f]{64}", frame["sha256"]):
        raise ValueError(f"Invalid SHA-256: {frame['path']}")
    path = (ROOT / frame["path"]).resolve()
    if not path.is_relative_to(ROOT / ".context"):
        raise ValueError(f"Screenshot must be inside the workspace .context: {frame['path']}")
    return path


def verify_capture(path, frame):
    raw = path.read_bytes()
    if raw[:16] != bytes.fromhex("89504e470d0a1a0a0000000d49484452"):
        raise ValueError(f"Invalid PNG: {frame['path']}")
    width, height = struct.unpack(">II", raw[16:24])
    if [width, height] != frame["viewport"] or sha256(raw).hexdigest() != frame["sha256"]:
        raise ValueError(f"Screenshot dimensions or digest changed: {frame['path']}")


def review_sample(data, verify_captures=False):
    counts, qualified = Counter(), Counter()
    seen = set()
    packets = []
    for row in data["records"]:
        required(row, ("name", "group", "post", "site", "status"))
        group, state = row["group"], row["status"]
        if group not in GROUPS or state not in STATES:
            raise ValueError(f"{row['name']}: unknown group or state")
        for key in ("post", "site"):
            target = urlsplit(row[key])
            if target.scheme != "https" or not target.hostname or target.username or target.password:
                raise ValueError(f"{row['name']}: {key} must be a public HTTPS link")
        target = urlsplit(row["site"])
        site_key = (target.hostname.removeprefix("www."), target.path.rstrip("/"))
        if site_key in seen:
            raise ValueError(f"{row['name']}: duplicate live site")
        seen.add(site_key)
        counts[group] += 1
        if state != "interaction-verified":
            required(row, ("observation",))
            continue
        required(row, ("action", "outcome", *PACKET))
        if not row.get("captures"):
            raise ValueError(f"{row['name']}: interaction has no original capture")
        for frame in row["captures"]:
            path = capture_path(frame)
            if verify_captures:
                verify_capture(path, frame)
        qualified[group] += 1
        packets.append({field: row[field] for field in ("name", "group", "site", "post", *PACKET)})
    return {
        "screened": dict(sorted(counts.items())),
        "interaction_verified": dict(sorted(qualified.items())),
        "sample_ready": all(counts[group] >= 4 and qualified[group] >= 2 for group in GROUPS),
        "builder_inputs": packets,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=HERE / "reference-sample.json")
    parser.add_argument("--verify-captures", action="store_true")
    args = parser.parse_args()
    try:
        result = review_sample(json.loads(args.manifest.read_text()), args.verify_captures)
    except (OSError, KeyError, ValueError, struct.error) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2))
    return 0 if result["sample_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
