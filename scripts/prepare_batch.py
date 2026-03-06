"""Prepare a batch of images for vision analysis. 
Usage: python prepare_batch.py <start_index> <batch_size>
Copies images to workspace/vbatch/ and prints the image_urls for mapping."""
import json, sys, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WORKSPACE = Path.home() / ".openclaw" / "workspace" / "vbatch"
BATCH_LIST = BASE / "data" / "batch_list.json"
VISION_RESULTS = BASE / "data" / "vision_results.json"

# Load already-processed
with open(VISION_RESULTS) as f:
    done = set(json.load(f).keys())

# Load full list
with open(BATCH_LIST) as f:
    all_items = json.load(f)

# Filter to unprocessed
remaining = [item for item in all_items if item["image_url"] not in done]

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
size = int(sys.argv[2]) if len(sys.argv) > 2 else 20

batch = remaining[start:start+size]

# Clean and copy
WORKSPACE.mkdir(parents=True, exist_ok=True)
for f in WORKSPACE.iterdir():
    f.unlink()

mapping = []
for i, item in enumerate(batch):
    src = Path(item["path"])
    # Use numbered prefix for ordering
    dest = WORKSPACE / f"{i:02d}_{src.name}"
    shutil.copy2(src, dest)
    mapping.append({"index": i, "image_url": item["image_url"], "name": item["name"], "file": dest.name})

# Save mapping
with open(WORKSPACE / "mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)

print(f"Prepared {len(batch)} images (from {len(remaining)} remaining)")
print(f"Files in: {WORKSPACE}")
for m in mapping:
    print(f"  {m['index']:2d}: {m['file']}")
