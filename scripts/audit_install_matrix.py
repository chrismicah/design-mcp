"""Check a complete verify_install_matrix.sh transcript and emit an install receipt."""

import argparse
import hashlib
import json
from pathlib import Path
import re


PYTHON_MINORS = ("3.10", "3.11", "3.12", "3.13")
DEFAULT_TOOLS = {"direct", "react", "check"}
COMPATIBILITY_TOOLS = DEFAULT_TOOLS | {
    "search_design_patterns", "get_design_blueprint", "get_semantic_tokens",
    "get_design_taxonomy", "get_behavioral_pattern", "compare_design_approaches",
    "analyze_and_devibecode", "get_design_system", "get_library_recommendations",
    "get_library_details", "scan_project", "generate_refactored_code",
    "get_visual_recipe", "get_visual_suggestions",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(raw, major, arch, revision):
    transcript = raw.decode("utf-8").replace("\r\n", "\n")
    hosts = list(re.finditer(r"^Host: (\S+) macOS ([\d.]+), Python ([\d.]+)$", transcript, re.M))
    require(len(hosts) == len(PYTHON_MINORS), "Expected one install log for each Python minor")
    preflight = transcript[:hosts[0].start()]
    versions = re.findall(r"^ProductVersion:[ \t]+([\d.]+)$", preflight, re.M)
    require(len(versions) == 1, "Expected one macOS product version")
    os_version = versions[0]
    require(os_version.startswith(f"{major}."), f"Observed macOS {os_version}, expected major {major}")
    for field, expected in (("Architecture", arch), ("Rosetta", "0"), ("Source commit", revision)):
        require(re.findall(rf"^{field}: (.+)$", preflight, re.M) == [expected], f"Unexpected {field}")
    lines = transcript.rstrip().splitlines()
    summary = lines[-1]
    # The original serial verifier abbreviated the same four cells as a range.
    valid_summaries = {
        f"PASS both installers and stdio smoke on macOS {os_version} {arch}, Python {minors}, source {revision}"
        for minors in (" ".join(PYTHON_MINORS), "3.10–3.13")
    }
    require(summary in valid_summaries and lines.count(summary) == 1,
            "Missing or incorrect final matrix result")

    cells = {}
    for index, (minor, host) in enumerate(zip(PYTHON_MINORS, hosts)):
        recorded_arch, recorded_os, python_version = host.groups()
        require((recorded_arch, recorded_os) == (arch, os_version) and python_version.startswith(minor + "."),
                f"Unexpected host or Python in the {minor} cell")
        end = hosts[index + 1].start() if index + 1 < len(hosts) else transcript.rfind(summary)
        cell = transcript[host.end():end]
        entry_points = list(re.finditer(r"^PASS installed entry point — design-mcp \S+ at (.+)$", cell, re.M))
        installers = [Path(entry[1]).parent.name for entry in entry_points]
        require(installers == ["pipx-bin", "uv-bin"], f"Python {minor}: expected distinct pipx and uv entry points")
        provenance = re.findall(r"^PASS pinned Git install — (.+)$", cell[:entry_points[0].start()], re.M)
        require(provenance == [revision, revision], f"Python {minor}: expected two pinned Git installs")
        for installer, start, stop in zip(("pipx", "uv"), entry_points, (entry_points[1].start(), len(cell))):
            report = cell[start.end():stop]
            label = f"Python {minor} via {installer}"
            require(report.splitlines().count("PASS stdio tools/call — direct returned direction") == 1,
                    f"{label}: expected a passing doctor call")
            batches = [json.loads(match[0]) for match in re.finditer(r'(?ms)^\{\n  "fastmcp".*?^\}', report)]
            require([batch["mode"] for batch in batches] == ["v2", "both"], f"{label}: missing a smoke report")
            for batch, names in zip(batches, (DEFAULT_TOOLS, COMPATIBILITY_TOOLS)):
                tools = batch["tools"]
                require(set(tools) == names and all(result["keys"] for result in tools.values()),
                        f"{label}: incomplete {batch['mode']} tool results")
        cells[minor] = {"python": python_version, "installers": ["pipx", "uv"], "smoke_tool_counts": [3, 17, 3, 17]}

    return {"macos": os_version, "arch": arch, "commit": revision, "transcript_sha256": hashlib.sha256(raw).hexdigest(),
            "cells": cells, "pinned_installs": 8, "doctor_passes": 8, "stdio_smoke_runs": 16}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("macos_major", type=int)
    parser.add_argument("arch", choices=("arm64", "x86_64"))
    parser.add_argument("commit")
    parser.add_argument("transcript", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit):
        parser.error("Pass the full pinned commit")
    try:
        receipt = audit(args.transcript.read_bytes(), args.macos_major, args.arch, args.commit)
    except (KeyError, TypeError, ValueError, OSError) as exc:
        parser.exit(1, f"Install matrix audit failed: {exc}\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
