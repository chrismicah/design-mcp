"""Explore the webui-7kbal dataset structure."""
import json
import os
from huggingface_hub import hf_hub_download

# Set HF_TOKEN as an environment variable before running

print("Downloading balanced_7k.json...")
path = hf_hub_download("biglab/webui-7kbal", "balanced_7k.json", repo_type="dataset")
print(f"Downloaded to: {path}")

with open(path) as f:
    data = json.load(f)

print(f"Type: {type(data)}")

if isinstance(data, list):
    print(f"Count: {len(data)}")
    if data:
        print(f"First entry keys: {list(data[0].keys())}")
        print("\n--- First 3 entries (truncated) ---")
        for i, entry in enumerate(data[:3]):
            print(f"\n=== Entry {i} ===")
            for k, v in entry.items():
                val_str = str(v)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                print(f"  {k}: {val_str}")
elif isinstance(data, dict):
    print(f"Top keys: {list(data.keys())[:20]}")
    for k in list(data.keys())[:3]:
        v = data[k]
        val_str = str(v)
        if len(val_str) > 200:
            val_str = val_str[:200] + "..."
        print(f"  {k}: {val_str}")
