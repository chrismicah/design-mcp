import json, os

with open('data/vision_results.json') as f:
    vision = json.load(f)
print(f'Vision results so far: {len(vision)}')

with open('data/patterns.json') as f:
    patterns = json.load(f)

analyzed_paths = set(vision.keys())

need_vision = []
for p in patterns:
    img = p.get('image_url') or ''
    if img.startswith('screenshots/') and img not in analyzed_paths:
        need_vision.append(p)

local_screenshots = sum(1 for p in patterns if (p.get('image_url') or '').startswith('screenshots/'))
print(f'Patterns with local screenshots: {local_screenshots}')
print(f'Already analyzed: {len(analyzed_paths)}')
print(f'Still need vision analysis: {len(need_vision)}')

existing = [p for p in need_vision if os.path.exists(p['image_url'])]
missing = len(need_vision) - len(existing)
print(f'  With existing files: {len(existing)}')
print(f'  Missing files: {missing}')

remaining = [{'id': p['id'], 'name': p['name'], 'image_url': p['image_url']} for p in existing]
with open('data/remaining_vision.json', 'w') as f:
    json.dump(remaining, f, indent=2)
print(f'Saved {len(remaining)} to data/remaining_vision.json')
