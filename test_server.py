"""Quick test to verify all server tools work."""
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
    print("Testing Design Intelligence MCP Server...")
    print("=" * 50)

    # Test 1: Taxonomy
    tax = await get_design_taxonomy()
    print(f"[OK] Taxonomy: {len(tax['page_types'])} page types, {len(tax['ui_elements'])} UI elements")

    # Test 2: Semantic Tokens
    tokens = await get_semantic_tokens()
    print(f"[OK] Tokens: sections = {list(tokens.keys())}")

    # Test 3: Behavioral Pattern
    bp = await get_behavioral_pattern("empty_state")
    print(f"[OK] Behavioral: empty_state -> {bp['reference']}")

    # Test 4: Behavioral Pattern (fuzzy)
    bp2 = await get_behavioral_pattern("loading")
    print(f"[OK] Behavioral fuzzy: 'loading' matched -> {list(bp2.keys())}")

    # Test 5: Search (empty DB)
    results = await search_design_patterns("dashboard")
    print(f"[OK] Search (empty db): {len(results)} results")

    # Test 6: Compare (empty DB)
    cmp = await compare_design_approaches("Dashboard")
    print(f"[OK] Compare: {cmp['summary']}")

    # Test 7: Get Blueprint (not found)
    missing = await get_design_blueprint("nonexistent-id")
    print(f"[OK] Blueprint missing: {missing}")

    print("=" * 50)
    print("All 7 tool tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
