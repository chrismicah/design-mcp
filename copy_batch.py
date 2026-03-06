import json, shutil, os

remaining = json.load(open('data/remaining_vision.json'))
dest = os.path.expanduser('~/.openclaw/workspace/vision_batch')
os.makedirs(dest, exist_ok=True)

# Copy first 5 images to workspace
for item in remaining[:5]:
    src = item['image_url']
    if os.path.exists(src):
        fname = os.path.basename(src)
        shutil.copy2(src, os.path.join(dest, fname))
        print(f"Copied: {fname}")

print(f"\nCopied to: {dest}")
