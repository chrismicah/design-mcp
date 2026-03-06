"""Prepare vision batches by copying images to workspace and generating manifest."""
import json, shutil, os, sys

REMAINING_PATH = 'data/remaining_vision.json'
VISION_RESULTS_PATH = 'data/vision_results.json'
WORKSPACE_BATCH = os.path.expanduser('~/.openclaw/workspace/vision_batch')
BATCH_SIZE = 20

def prep_batch(batch_num=0):
    with open(REMAINING_PATH) as f:
        remaining = json.load(f)
    
    with open(VISION_RESULTS_PATH) as f:
        existing = json.load(f)
    
    # Filter out already processed
    todo = [r for r in remaining if r['image_url'] not in existing]
    
    if not todo:
        print("ALL_DONE")
        return
    
    # Get batch
    start = batch_num * BATCH_SIZE
    batch = todo[start:start + BATCH_SIZE]
    
    if not batch:
        print("ALL_DONE")
        return
    
    # Clean and copy
    if os.path.exists(WORKSPACE_BATCH):
        shutil.rmtree(WORKSPACE_BATCH)
    os.makedirs(WORKSPACE_BATCH)
    
    manifest = []
    for item in batch:
        src = item['image_url']
        if os.path.exists(src):
            fname = os.path.basename(src)
            dest = os.path.join(WORKSPACE_BATCH, fname)
            shutil.copy2(src, dest)
            manifest.append({
                'id': item['id'],
                'name': item['name'],
                'image_url': item['image_url'],
                'workspace_path': dest.replace('\\', '/')
            })
    
    with open(os.path.join(WORKSPACE_BATCH, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"BATCH_READY:{len(manifest)}:{len(todo) - len(manifest)}")
    for m in manifest:
        print(m['workspace_path'])

if __name__ == '__main__':
    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    prep_batch(batch_num)
