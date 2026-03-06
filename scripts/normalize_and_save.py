"""Normalize raw vision results and save to vision_results.json."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_vision import normalize

VISION_RESULTS_PATH = 'data/vision_results.json'
WORKSPACE_BATCH = os.path.expanduser('~/.openclaw/workspace/vision_batch')

def save(raw_json_str):
    raw = json.loads(raw_json_str)
    normalized = normalize(raw)
    
    with open(VISION_RESULTS_PATH) as f:
        existing = json.load(f)
    
    with open(os.path.join(WORKSPACE_BATCH, 'manifest.json')) as f:
        manifest = json.load(f)
    
    saved = 0
    for i, result in enumerate(normalized):
        if i < len(manifest):
            key = manifest[i]['image_url']
            existing[key] = result
            saved += 1
    
    with open(VISION_RESULTS_PATH, 'w') as f:
        json.dump(existing, f, indent=2)
    
    remaining = 742 - len(existing)
    print(f"Saved {saved}. Total: {len(existing)}/742. Remaining: {remaining}")

if __name__ == '__main__':
    save(sys.stdin.read())
