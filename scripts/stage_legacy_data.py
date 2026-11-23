"""Seed writable inputs for the historical corpus maintenance scripts."""

from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile


ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "anti_generic_system.json",
    "anti_pattern_fixes.json",
    "behavioral_templates.json",
    "component_code.json",
    "decision_trees.json",
    "decision_trees_indexed.json",
    "layout_templates.json",
    "libraries.json",
    "patterns.json",
    "taxonomy.json",
    "tokens/semantic_tokens.json",
    "tokens/token_sets.json",
    "vision_results.json",
    "visual_recipes.json",
)


def stage(source: Path, output: Path) -> list[str]:
    """Copy missing inputs without replacing an existing working file."""
    missing = [name for name in INPUTS if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(f"A source checkout is required. Missing: {', '.join(missing)}")

    copied = []
    for name in INPUTS:
        target = output / name
        if target.exists() or target.is_symlink():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with (source / name).open("rb") as original, NamedTemporaryFile(dir=target.parent) as scratch:
            shutil.copyfileobj(original, scratch)
            scratch.flush()
            try:
                target.hardlink_to(scratch.name)
            except FileExistsError:
                continue
        copied.append(name)
    return copied


if __name__ == "__main__":
    copied = stage(ROOT / "design_mcp" / "data", ROOT / "data")
    print(f"Staged {len(copied)} writable files in data/. Existing files were preserved.")
