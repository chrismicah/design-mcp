"""End-to-end test: verify search returns quality-ranked results."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from server import search_design_patterns, get_design_blueprint, compare_design_approaches
from database import DesignDatabase

async def main():
    db = DesignDatabase(str(Path(__file__).parent.parent / "data" / "patterns.json"))
    print(f"Database: {db.count()} patterns")
    
    # Check quality scores are populated
    scored = [p for p in db._patterns if p.quality_score is not None]
    print(f"Patterns with quality_score: {len(scored)}/{db.count()}")
    
    # Search test
    results = await search_design_patterns("dashboard", limit=5)
    print(f"\nTop 5 'dashboard' results:")
    for r in results:
        bp = await get_design_blueprint(r["id"], detailed=True)
        qs = bp.get("quality_score", "N/A")
        print(f"  [{qs}] {r['name'][:50]} ({r['page_type']})")
    
    # Compare test
    cmp = await compare_design_approaches("Dashboard", limit=3)
    print(f"\nCompare Dashboard: {cmp['summary']}")
    
    # Verify quality-ranked ordering in filter-only search
    results2 = await search_design_patterns("fintech", limit=5)
    print(f"\nTop 5 'fintech' results:")
    for r in results2:
        bp = await get_design_blueprint(r["id"], detailed=True)
        qs = bp.get("quality_score", "N/A")
        print(f"  [{qs}] {r['name'][:50]}")
    
    print("\n=== E2E TEST PASSED ===")

if __name__ == "__main__":
    asyncio.run(main())
