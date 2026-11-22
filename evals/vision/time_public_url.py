"""Compare two installed public-URL review CLIs on one owned browser runner."""

import argparse
import json
import math
import os
from pathlib import Path
import signal
from statistics import median
import subprocess
import tempfile
from time import monotonic

URL = "https://designsystem.digital.gov/templates/form-templates/address-form/"
PAIRS = 10
METRICS = ("wall_ms", "page_load_ms", "capture_ms")


def capture(executable, chrome, playwriter, out):
    with tempfile.TemporaryDirectory(dir=out) as scratch:
        args = [str(executable), "review", URL, "--playwriter", str(playwriter), "--chrome", str(chrome),
                "--out", str(Path(scratch) / "review"), "--json"]
        started = monotonic()
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
                              env={**os.environ, "TMPDIR": scratch}) as process:
            try:
                stdout, stderr = process.communicate(timeout=100)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
                return {"error": "review timed out"}
        elapsed_ms = round((monotonic() - started) * 1000)
        if process.returncode != 0:
            return {"error": stderr.strip()[-800:], "exit_code": process.returncode}
        result = json.loads(stdout)
        preview = Path(scratch) / "review" / result["capture_id"]
        evidence = json.loads((preview / "evidence.json").read_bytes())
        frames = sorted(evidence["frames"], key=lambda frame: frame["viewport"]["width"])
        assert result["ok"] and result["frontier"]["status"] == "not-run" and (preview / "preview.html").is_file()
        assert [(f["viewport"]["width"], f["viewport"]["height"]) for f in frames] == [(390, 844), (1440, 900)]
        assert all(f["masks"]["applied"] and f["masks"]["counts"]["field"] > 0 for f in frames)
    trial = {"wall_ms": elapsed_ms, "page_load_ms": result["timings_ms"]["page_load"],
             "capture_ms": result["timings_ms"]["capture"], "masked_fields": result["masked"]["field"],
             "frame_sha256": [f["screenshot"]["sha256"] for f in frames]}
    if "url_capture_ms" in result:
        profile = result["url_capture_ms"]
        viewports = profile["viewports"]
        assert [view["width"] for view in viewports] == [1440, 390]
        assert max(view["page_load"] for view in viewports) == trial["page_load_ms"]
        assert sum(view["capture"] for view in viewports) == trial["capture_ms"]
        assert profile["session_ready"] <= profile["drive"]
        assert profile["local_decision"] <= profile["preview_written"] + 0.2 <= elapsed_ms + 0.2
        trial["url_capture_ms"] = profile
    return trial


def stats(values):
    return {"median": median(values), "p95": sorted(values)[math.ceil(0.95 * len(values)) - 1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "chrome", "playwriter", "out"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    arms = {name: getattr(args, name) for name in ("before", "after")}
    browser = subprocess.check_output([args.chrome, "--version"], text=True).strip()
    playwriter = subprocess.check_output([args.playwriter, "--version"], text=True).strip()
    assert browser.endswith("158.0.8127.36") and playwriter == "0.12.0"
    report = {"url": URL, "browser": browser, "playwriter": playwriter,
              "macos": subprocess.check_output(["sw_vers", "-productVersion"], text=True).strip(),
              "architecture": os.uname().machine, "expected_pairs": PAIRS, "pairs": []}
    try:
        for index in range(PAIRS):
            order = list(arms) if index % 2 == 0 else list(reversed(arms))
            pair = {"order": order}
            report["pairs"].append(pair)
            for arm in order:
                pair[arm] = capture(arms[arm], args.chrome, args.playwriter, args.out.parent)
                print(json.dumps({"pair": index + 1, "arm": arm, **pair[arm]}), flush=True)
                if "error" in pair[arm]:
                    raise RuntimeError(f"Review failed on pair {index + 1} in {arm}")
            assert "url_capture_ms" in pair["after"]
            assert "startup" in pair["after"]["url_capture_ms"]
        pairs = report["pairs"]
        report["identical_capture_pairs"] = sum(p["before"]["frame_sha256"] == p["after"]["frame_sha256"] for p in pairs)
        report["summary"] = {metric: {**{arm: stats([p[arm][metric] for p in pairs]) for arm in arms},
                                      "paired_median_change": median(p["after"][metric] - p["before"][metric]
                                                                     for p in pairs)} for metric in METRICS}
    finally:
        args.out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
