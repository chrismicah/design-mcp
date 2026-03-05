"""
Optional: Use Claude API to enrich scraped design patterns with
behavioral descriptions, layout analysis, and component hints.

Run this after the initial scraping phase to fill metadata gaps.
Requires: ANTHROPIC_API_KEY environment variable
"""

import json
import httpx
import os
from schema import DesignPattern

ENRICHMENT_PROMPT = """You are a Senior UI/UX Analyst. Given a design pattern entry with partial metadata, fill in the missing fields.

Current data:
{pattern_json}

Fill in any missing fields from this list. Be specific and actionable:
- layout_type: one of [flexbox, css_grid, bento_grid, single_column, sidebar_main, split_screen, masonry, stacked]
- layout_notes: Brief description of the layout structure
- behavioral_description: How this pattern behaves (loading, empty, error states)
- component_hints: List of key components with their likely props
- accessibility_notes: Key WCAG requirements for this pattern
- semantic_tokens: Inferred spacing, color, and typography tokens

Return ONLY valid JSON matching the original schema. Do not include fields you cannot confidently determine."""


async def enrich_pattern(pattern: DesignPattern) -> dict:
    """Call Claude API to enrich a pattern's metadata."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1000,
                "messages": [{
                    "role": "user",
                    "content": ENRICHMENT_PROMPT.format(
                        pattern_json=pattern.model_dump_json(indent=2, exclude_none=True)
                    )
                }]
            }
        )
        result = response.json()
        return json.loads(result["content"][0]["text"])


async def enrich_batch(patterns: list[DesignPattern], max_count: int = 50) -> list[dict]:
    """Enrich a batch of patterns. Processes sequentially to avoid rate limits."""
    enriched = []
    for i, pattern in enumerate(patterns[:max_count]):
        try:
            result = await enrich_pattern(pattern)
            enriched.append(result)
            print(f"Enriched {i+1}/{min(len(patterns), max_count)}: {pattern.name}")
        except Exception as e:
            print(f"Failed to enrich {pattern.id}: {e}")
            enriched.append(pattern.model_dump())
    return enriched
