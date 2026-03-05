"""Fast ingestion of remaining webui-7kbal samples. Collects all in memory, saves once."""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from scripts.ingest_webui7k import DATASET_DIR, process_sample

DB_PATH = Path(__file__).parent.parent / "data" / "patterns.json"

def main():
    # Load existing
    with open(DB_PATH) as f:
        existing = json.load(f)
    
    existing_ids = {p["id"] for p in existing}
    print(f"Existing: {len(existing)} patterns ({len(existing_ids)} unique IDs)", flush=True)

    sample_dirs = sorted([d for d in DATASET_DIR.iterdir() if d.is_dir()])
    print(f"Total sample dirs: {len(sample_dirs)}", flush=True)

    new_patterns = []
    skipped = 0
    errors = 0

    for i, d in enumerate(sample_dirs):
        test_id = f"webui7k-{d.name}"
        if test_id in existing_ids:
            skipped += 1
            continue

        try:
            pattern = process_sample(d)
            if pattern is None:
                skipped += 1
                continue
            new_patterns.append(pattern.model_dump())
            existing_ids.add(pattern.id)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error on {d.name}: {e}", flush=True)

        if len(new_patterns) % 200 == 0 and len(new_patterns) > 0:
            print(f"  Processed {i+1}/{len(sample_dirs)}, new: {len(new_patterns)}, skipped: {skipped}, errors: {errors}", flush=True)

    print(f"\nCollected {len(new_patterns)} new patterns. Saving...", flush=True)
    
    # Combine and save once (no indent for speed)
    all_patterns = existing + new_patterns
    with open(DB_PATH, "w") as f:
        json.dump(all_patterns, f, indent=2)
    
    print(f"Done! Total: {len(all_patterns)} patterns", flush=True)
    print(f"  New: {len(new_patterns)}, Skipped: {skipped}, Errors: {errors}", flush=True)

if __name__ == "__main__":
    main()
