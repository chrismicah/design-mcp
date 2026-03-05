"""Full integration test with seed data."""
import asyncio
from server import (
    search_design_patterns,
    get_design_blueprint,
    get_semantic_tokens,
    get_design_taxonomy,
    get_behavioral_pattern,
    compare_design_approaches,
)

async def main():
    print("Testing Design Intelligence MCP Server with seed data...")
    print("=" * 60)

    # Test 1: Search for dark mode dashboards
    print("\n[Test 1] Search: 'dark mode dashboard fintech'")
    results = await search_design_patterns("dark mode dashboard fintech")
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"    - {r['name']} ({r.get('color_mode', 'n/a')})")

    # Test 2: Search by page type
    print("\n[Test 2] Search by page_type='Pricing'")
    results = await search_design_patterns("pricing", page_type="Pricing")
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"    - {r['name']}")

    # Test 3: Search by industry
    print("\n[Test 3] Search by industry='Fintech'")
    results = await search_design_patterns("dashboard", industry="Fintech")
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"    - {r['name']}")

    # Test 4: Get detailed blueprint
    print("\n[Test 4] Get detailed blueprint for 'seed-stripe-dashboard'")
    bp = await get_design_blueprint("seed-stripe-dashboard", detailed=True)
    print(f"  Fields: {list(bp.keys())}")
    print(f"  Layout: {bp.get('layout_type')}")
    print(f"  Components: {len(bp.get('component_hints', []))}")

    # Test 5: Compare dashboards
    print("\n[Test 5] Compare dashboard approaches")
    cmp = await compare_design_approaches("Dashboard")
    print(f"  Examples: {len(cmp['examples'])}")
    print(f"  Summary: {cmp['summary']}")

    # Test 6: Get behavioral pattern
    print("\n[Test 6] Behavioral: 'empty_state'")
    bp = await get_behavioral_pattern("empty_state")
    print(f"  Best practice: {bp['best_practice'][:80]}...")

    # Test 7: Search with visual style filter
    print("\n[Test 7] Search with visual_style='Glassmorphism'")
    results = await search_design_patterns("pricing", visual_style="Glassmorphism")
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"    - {r['name']} ({r.get('visual_style', [])})")

    # Test 8: Get taxonomy
    print("\n[Test 8] Taxonomy")
    tax = await get_design_taxonomy()
    print(f"  {len(tax['page_types'])} page types, {len(tax['ui_elements'])} UI elements")

    # Test 9: Search with field filtering
    print("\n[Test 9] Search with field filtering (layout_type + ui_elements only)")
    results = await search_design_patterns("dashboard", fields=["layout_type", "ui_elements"])
    print(f"  Found {len(results)} results")
    for r in results:
        print(f"    - id={r['id']}, layout={r.get('layout_type')}, elements={len(r.get('ui_elements', []))}")

    print("\n" + "=" * 60)
    print("All integration tests passed! Server is ready.")


if __name__ == "__main__":
    asyncio.run(main())
