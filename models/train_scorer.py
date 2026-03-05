"""
Run the quality scorer across all patterns and update quality_score in patterns.json.
Also prints a distribution summary.
"""
import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema import DesignPattern
from models.quality_scorer import score_pattern


def main():
    data_path = Path(__file__).parent.parent / "data" / "patterns.json"

    print(f"Loading patterns from {data_path}...")
    with open(data_path) as f:
        raw = json.load(f)

    patterns = [DesignPattern(**d) for d in raw]
    print(f"Loaded {len(patterns)} patterns.")

    # Score all patterns
    scores = []
    for p in patterns:
        s = score_pattern(p)
        p.quality_score = s
        scores.append(s)

    # Save back
    with open(data_path, "w") as f:
        json.dump([p.model_dump() for p in patterns], f, indent=2)
    print(f"Updated quality_score for all {len(patterns)} patterns.\n")

    # Print distribution summary
    print_distribution(scores)


def print_distribution(scores: list[float]):
    """Print a histogram-style summary of score distribution."""
    buckets = {
        "0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0,
        "5-6": 0, "6-7": 0, "7-8": 0, "8-9": 0, "9-10": 0,
    }
    for s in scores:
        if s >= 9:
            buckets["9-10"] += 1
        elif s >= 8:
            buckets["8-9"] += 1
        elif s >= 7:
            buckets["7-8"] += 1
        elif s >= 6:
            buckets["6-7"] += 1
        elif s >= 5:
            buckets["5-6"] += 1
        elif s >= 4:
            buckets["4-5"] += 1
        elif s >= 3:
            buckets["3-4"] += 1
        elif s >= 2:
            buckets["2-3"] += 1
        elif s >= 1:
            buckets["1-2"] += 1
        else:
            buckets["0-1"] += 1

    avg = sum(scores) / len(scores) if scores else 0
    mn = min(scores) if scores else 0
    mx = max(scores) if scores else 0

    print("=" * 50)
    print("  QUALITY SCORE DISTRIBUTION")
    print("=" * 50)
    max_count = max(buckets.values()) if buckets.values() else 1
    for label, count in buckets.items():
        bar = "#" * int(40 * count / max_count) if max_count > 0 else ""
        print(f"  {label:>5}: {bar} {count}")
    print("-" * 50)
    print(f"  Total: {len(scores)}")
    print(f"  Mean:  {avg:.2f}")
    print(f"  Min:   {mn:.2f}")
    print(f"  Max:   {mx:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
