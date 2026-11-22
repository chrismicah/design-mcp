"""Compare alternating first toolbar activations with the collector eager or on demand."""

from collections import Counter
from hashlib import sha256
import json
from math import ceil, isfinite
from pathlib import Path
from random import Random
from statistics import median
import sys


ARMS = ("eager", "on-demand")
METRICS = ("openMs", "scanMs", "firstScanToMissingHostMs", "popupTargetObservedMs")
MIN_OPEN_IMPROVEMENT_MS = 20
SCAN_REGRESSION_LIMIT_MS = 20


def p95(values):
    return sorted(values)[ceil(0.95 * len(values)) - 1]


def positive_number(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def summarize(root, count, version):
    rows = []
    for pair in range(1, count + 1):
        for arm in ARMS:
            receipt = root / f"sample-{pair}-{arm}" / "extension-review.json"
            data = receipt.read_bytes() if receipt.is_file() else b""
            raw = json.loads(data) if data else {}
            timings = raw.get("firstActivation", {})
            nav = raw.get("popupNavigation", {})
            passed = (
                raw.get("browserChecksPassed") is True and raw.get("browser") == f"Chrome/{version}"
                and raw.get("collectorMode") == arm and raw.get("extensionId") == raw.get("pinnedId")
                and nav.get("collectorPresent") is (arm == "eager")
                and timings.get("drivers", {}).get("open") == "macOS pointer"
                and all(positive_number(timings.get(k)) for k in METRICS)
            )
            error = raw.get("error")
            rows.append({"pair": pair, "arm": arm, "passed": passed, "timings": timings, "navigation": nav,
                         "phase": raw.get("phase"), "error": error or (None if passed else "Missing or invalid timing evidence"),
                         "profile": raw.get("chromeProfile"), "receipt_sha256": sha256(data).hexdigest() if data else None})
    profile_count = len({row["profile"] for row in rows if row["profile"]})
    report = {
        "scope": "Alternating eager and on-demand collector variants on the same hosted macOS runner.",
        "expected_pairs": count,
        "distinct_profiles": profile_count,
        "passed_by_arm": dict(Counter(row["arm"] for row in rows if row["passed"])),
        "trials": rows,
    }
    mask_receipts = {arm: root / "saved-preview" / arm / "extension-review.json" for arm in ARMS}
    masks = {arm: json.loads(path.read_bytes()) if path.is_file() else {} for arm, path in mask_receipts.items()}
    report["redaction_verified_by_arm"] = {
        arm: receipt.get("collectorMode") == arm and receipt.get("verifiedMaskInterior") is True
        and receipt.get("privateValueAbsentFromArtifacts") is True
        for arm, receipt in masks.items()
    }
    complete = count >= 30 and profile_count == 2 * count and all(row["passed"] for row in rows)
    report["complete"] = complete
    if not complete:
        return report
    arms = {arm: [row["timings"] for row in rows if row["arm"] == arm] for arm in ARMS}
    timing_p95 = {arm: {key: p95([row[key] for row in timings]) for key in METRICS} for arm, timings in arms.items()}
    differences = [base["openMs"] - variant["openMs"] for base, variant in zip(*arms.values(), strict=True)]
    rng = Random(20261122)
    draws = sorted(median(rng.choices(differences, k=count)) for _ in range(10000))
    lower, upper = draws[250], draws[9750]
    base, variant = (timing_p95[arm] for arm in ARMS)
    passed = (
        all(report["redaction_verified_by_arm"].values())
        and base["openMs"] - variant["openMs"] >= MIN_OPEN_IMPROVEMENT_MS and lower > 0
        and all(variant[k] <= min(1000, base[k] + SCAN_REGRESSION_LIMIT_MS)
                for k in ("firstScanToMissingHostMs", "scanMs"))
    )
    report.update(p95=timing_p95, paired_median_open_improvement_ms=median(differences),
                  paired_bootstrap_95_interval_ms=[lower, upper], retain_candidate=passed)
    return report


def main():
    root, count, version = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    result = summarize(root, count, version)
    (root / "collector-timing-series.json").write_text(json.dumps(result, indent=2) + "\n")
    print({k: v for k, v in result.items() if k != "trials"})
    if not result["complete"] or not all(result["redaction_verified_by_arm"].values()):
        raise SystemExit("One or more verification trials did not complete")


if __name__ == "__main__":
    main()
