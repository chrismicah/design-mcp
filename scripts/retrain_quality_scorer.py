"""
Retrain the design quality scorer on all patterns.
Scores patterns 0-10 based on metadata completeness, source quality, and design signals.
"""
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = Path(__file__).parent.parent / "data" / "patterns.json"


def score_pattern(p: dict) -> float:
    """Score a design pattern 0-10 based on quality signals."""
    score = 0.0
    
    # Source quality (max 2.0)
    source_scores = {
        "curated": 2.0,      # Hand-picked
        "awwwards": 1.8,     # Award-winning
        "dribbble": 1.5,     # Professional designers
        "landbook": 1.2,     # Curated gallery
        "webui-7kbal": 1.0,  # Dataset (mixed quality)
    }
    score += source_scores.get(p.get("source", ""), 0.5)
    
    # Metadata completeness (max 3.0)
    completeness = 0.0
    if p.get("page_type") and p["page_type"] != "Landing Page":
        completeness += 0.5  # Specific page type identified
    if p.get("industry"):
        completeness += 0.4
    if p.get("layout_type"):
        completeness += 0.5
    if p.get("color_mode"):
        completeness += 0.3
    if len(p.get("ui_elements", [])) >= 3:
        completeness += 0.5
    elif len(p.get("ui_elements", [])) >= 1:
        completeness += 0.2
    if len(p.get("visual_style", [])) >= 1:
        completeness += 0.3
    if p.get("behavioral_description"):
        completeness += 0.5
    score += min(completeness, 3.0)
    
    # Design diversity signals (max 2.0)
    diversity = 0.0
    if len(p.get("ux_patterns", [])) >= 2:
        diversity += 0.5
    if len(p.get("component_hints", [])) >= 1:
        diversity += 0.5
    if p.get("accessibility_notes"):
        diversity += 0.5
    if p.get("semantic_tokens"):
        diversity += 0.5
    score += min(diversity, 2.0)
    
    # Image quality signal (max 1.0)
    if p.get("image_url"):
        score += 0.5
        # Screenshots from design galleries tend to be higher quality
        if any(x in str(p.get("image_url", "")) for x in ["awwwards", "dribbble", "curated"]):
            score += 0.5
    
    # Tag richness (max 1.0)
    tags = p.get("tags", [])
    if len(tags) >= 5:
        score += 1.0
    elif len(tags) >= 3:
        score += 0.5
    elif len(tags) >= 1:
        score += 0.2
    
    # Name quality (max 1.0)
    name = p.get("name", "")
    if len(name) > 10 and not name.startswith("WebUI Sample"):
        score += 0.5
        if any(x in name.lower() for x in ["dashboard", "landing", "app", "platform", "studio"]):
            score += 0.5
    
    return round(min(score, 10.0), 2)


def main():
    print("Retraining quality scorer...", flush=True)
    
    with open(DB_PATH) as f:
        patterns = json.load(f)
    
    print(f"Scoring {len(patterns)} patterns...", flush=True)
    
    scores = []
    for p in patterns:
        p["quality_score"] = score_pattern(p)
        scores.append(p["quality_score"])
    
    # Sort by quality score descending for better search results
    patterns.sort(key=lambda p: -(p.get("quality_score") or 0))
    
    with open(DB_PATH, "w") as f:
        json.dump(patterns, f, indent=2)
    
    # Stats
    avg = sum(scores) / len(scores)
    high = sum(1 for s in scores if s >= 7)
    mid = sum(1 for s in scores if 4 <= s < 7)
    low = sum(1 for s in scores if s < 4)
    
    print(f"\n=== Quality Score Distribution ===", flush=True)
    print(f"  Average: {avg:.2f}", flush=True)
    print(f"  High (7-10): {high}", flush=True)
    print(f"  Medium (4-7): {mid}", flush=True)
    print(f"  Low (0-4): {low}", flush=True)
    print(f"  Top 5:", flush=True)
    for p in patterns[:5]:
        print(f"    {p['quality_score']:.1f} - {p['name'][:60]} ({p['source']})", flush=True)
    
    print(f"\nDone! All {len(patterns)} patterns rescored and sorted.", flush=True)


if __name__ == "__main__":
    main()
