"""Optimize patterns.json: compress tokens, trim low-quality patterns."""
import json
import os
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"

patterns = json.load(open(DATA_DIR / "patterns.json"))
print(f"Input: {len(patterns)} patterns, {os.path.getsize(DATA_DIR / 'patterns.json') / 1024 / 1024:.1f} MB")

# Deduplicate token sets: many patterns share the same tokens
# Store unique token sets and reference by index
unique_tokens = {}
token_refs = []

for p in patterns:
    tokens = p.get("semantic_tokens", {})
    if isinstance(tokens, dict):
        # Create a hashable key
        key = json.dumps(tokens, sort_keys=True)
        if key not in unique_tokens:
            unique_tokens[key] = len(unique_tokens)
        token_refs.append(unique_tokens[key])
    else:
        token_refs.append(-1)

print(f"Unique token sets: {len(unique_tokens)} (from {len(patterns)} patterns)")

# Save token sets separately
token_list = [None] * len(unique_tokens)
for key_str, idx in unique_tokens.items():
    token_list[idx] = json.loads(key_str)

with open(DATA_DIR / "tokens" / "token_sets.json", "w") as f:
    json.dump(token_list, f, separators=(",", ":"))

# Replace inline tokens with index reference
for i, p in enumerate(patterns):
    ref = token_refs[i]
    if ref >= 0:
        p["semantic_tokens"] = ref  # Just the index

# Also compress decision trees (shared across page types)
unique_trees = {}
for p in patterns:
    tree = p.get("decision_tree")
    if tree:
        key = json.dumps(tree, sort_keys=True)
        if key not in unique_trees:
            unique_trees[key] = len(unique_trees)
        p["decision_tree"] = unique_trees[key]

tree_list = [None] * len(unique_trees)
for key_str, idx in unique_trees.items():
    tree_list[idx] = json.loads(key_str)

with open(DATA_DIR / "decision_trees_indexed.json", "w") as f:
    json.dump(tree_list, f, indent=2)

# Remove shade_scale (can be regenerated) to save space
for p in patterns:
    p.pop("primary_shade_scale", None)

# Remove empty fields to save space
for p in patterns:
    for key in list(p.keys()):
        val = p[key]
        if val is None or val == "" or val == [] or val == {}:
            del p[key]

# Save optimized
with open(DATA_DIR / "patterns.json", "w") as f:
    json.dump(patterns, f, separators=(",", ":"))

final_size = os.path.getsize(DATA_DIR / "patterns.json") / 1024 / 1024
token_size = os.path.getsize(DATA_DIR / "tokens" / "token_sets.json") / 1024 / 1024
print(f"Output: {len(patterns)} patterns, {final_size:.1f} MB + {token_size:.1f} MB tokens")
print(f"Total: {final_size + token_size:.1f} MB (was 20.6 MB)")
