"""Save vision results from a batch back to the main results file."""
import json, sys, os

VISION_RESULTS_PATH = 'data/vision_results.json'
WORKSPACE_BATCH = os.path.expanduser('~/.openclaw/workspace/vision_batch')

def save_results(results_json):
    """Save JSON results string to vision_results.json, keyed by image_url."""
    with open(VISION_RESULTS_PATH) as f:
        existing = json.load(f)
    
    with open(os.path.join(WORKSPACE_BATCH, 'manifest.json')) as f:
        manifest = json.load(f)
    
    results = json.loads(results_json)
    
    saved = 0
    for i, result in enumerate(results):
        if i < len(manifest):
            key = manifest[i]['image_url']
            existing[key] = result
            saved += 1
    
    with open(VISION_RESULTS_PATH, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"Saved {saved} results. Total: {len(existing)}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        save_results(sys.argv[1])
    else:
        # Read from stdin
        data = sys.stdin.read()
        save_results(data)
