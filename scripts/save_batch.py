"""Save vision batch results. Reads mapping.json and batch_results.json, merges into vision_results.json.
Auto-normalizes free-form labels to constrained schema."""
import json, sys
from pathlib import Path
from normalize_results import normalize

BASE = Path(__file__).resolve().parent.parent
WORKSPACE = Path.home() / ".openclaw" / "workspace" / "vbatch"
VISION_RESULTS = BASE / "data" / "vision_results.json"

# Load mapping
with open(WORKSPACE / "mapping.json") as f:
    mapping = json.load(f)

# Load existing results
with open(VISION_RESULTS) as f:
    results = json.load(f)

# Read new results from batch_results.json in workspace
with open(WORKSPACE / "batch_results.json") as f:
    raw_results = json.load(f)

# Normalize
new_results = normalize(raw_results)

# Map by index
for i, analysis in enumerate(new_results):
    if i < len(mapping):
        image_url = mapping[i]["image_url"]
        results[image_url] = analysis

with open(VISION_RESULTS, "w") as f:
    json.dump(results, f, indent=2)

print(f"Saved {len(new_results)} results. Total: {len(results)}")
