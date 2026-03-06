"""Optimize patterns.json by moving repeated data to separate files."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PATTERNS = BASE / "data" / "patterns.json"

with open(PATTERNS) as f:
    patterns = json.load(f)

# Instead of duplicating tokens in every pattern, use a reference
# Store: "semantic_tokens": "light" or "semantic_tokens": "dark"
light_tokens = None
dark_tokens = None

for p in patterns:
    tokens = p.get("semantic_tokens")
    if isinstance(tokens, dict) and "color-background" in tokens:
        if "84% 4.9%" in str(tokens.get("color-background", "")):
            dark_tokens = tokens
            p["semantic_tokens"] = "dark"
        else:
            light_tokens = tokens
            p["semantic_tokens"] = "light"

# Save token sets separately
tokens_dir = BASE / "data" / "tokens"
tokens_dir.mkdir(exist_ok=True)

if light_tokens:
    with open(tokens_dir / "semantic_tokens.json", "w") as f:
        json.dump({"light": light_tokens, "dark": dark_tokens}, f, indent=2)
    print(f"Saved token sets to data/tokens/semantic_tokens.json")

# Also trim component code duplicates - store as references
# Layout notes for same page type are identical, store once
layout_templates = {}
for p in patterns:
    notes = p.get("layout_notes", "")
    if notes and "className" in notes:
        page_type = p.get("page_type", "")
        if page_type not in layout_templates:
            layout_templates[page_type] = notes
        # Replace with reference
        p["layout_notes"] = f"[template:{page_type}]"

# Save layout templates
with open(BASE / "data" / "layout_templates.json", "w") as f:
    json.dump(layout_templates, f, indent=2)
print(f"Saved {len(layout_templates)} layout templates")

# Save behavioral templates (deduplicate)
behavior_templates = {}
for p in patterns:
    desc = p.get("behavioral_description", "")
    if desc:
        page_type = p.get("page_type", "")
        if page_type not in behavior_templates:
            behavior_templates[page_type] = {
                "behavioral_description": desc,
                "accessibility_notes": p.get("accessibility_notes", ""),
            }
        # Keep first 100 chars inline, full template is in the file
        # Actually, keep the full text - it's what agents need

# Save
with open(BASE / "data" / "behavioral_templates.json", "w") as f:
    json.dump(behavior_templates, f, indent=2)
print(f"Saved {len(behavior_templates)} behavioral templates")

# Also deduplicate component code hints
code_templates = {}
for p in patterns:
    hints = p.get("component_hints", [])
    for h in hints:
        code = h.get("code", "")
        name = h.get("name", "")
        if code and name not in code_templates:
            code_templates[name] = {"code": code, "library": h.get("library", "")}
        if code:
            # Replace inline code with reference
            h["code"] = f"[component:{name}]"

with open(BASE / "data" / "component_code.json", "w") as f:
    json.dump(code_templates, f, indent=2)
print(f"Saved {len(code_templates)} component code templates")

# Save optimized patterns
with open(PATTERNS, "w") as f:
    json.dump(patterns, f, indent=2)

size_mb = PATTERNS.stat().st_size / (1024*1024)
print(f"patterns.json: {size_mb:.1f} MB")
