import json
from pathlib import Path
from .schema import DesignPattern
from typing import Optional


class DesignDatabase:
    """
    Simple JSON-based design pattern database.
    For a production system, replace with vector search (e.g., ChromaDB).
    This is optimized for the 24-hour build timeline.
    """

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._patterns: list[DesignPattern] = []
        self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path) as f:
                data = json.load(f)
            self._patterns = [DesignPattern(**d) for d in data]

    def _save(self):
        with open(self.path, "w") as f:
            json.dump([p.model_dump() for p in self._patterns], f, indent=2)

    def add(self, pattern: DesignPattern):
        self._patterns.append(pattern)

    def add_batch(self, patterns: list[DesignPattern]):
        """Add multiple patterns and save once (much faster for bulk ingestion)."""
        self._patterns.extend(patterns)
        self._save()

    def save(self):
        """Explicit save for batch operations."""
        self._save()

    def get(self, pattern_id: str) -> Optional[DesignPattern]:
        for p in self._patterns:
            if p.id == pattern_id:
                return p
        return None

    def count(self) -> int:
        return len(self._patterns)

    def search(
        self,
        query: Optional[str] = None,
        page_type: Optional[str] = None,
        platform: Optional[str] = None,
        industry: Optional[str] = None,
        color_mode: Optional[str] = None,
        visual_style: Optional[str] = None,
        limit: int = 5
    ) -> list[DesignPattern]:
        results = self._patterns

        if page_type:
            results = [p for p in results if p.page_type.lower() == page_type.lower()]

        if platform:
            results = [p for p in results if p.platform.value == platform.lower()]

        if industry:
            results = [p for p in results if p.industry and industry.lower() in p.industry.lower()]

        if color_mode:
            results = [p for p in results if p.color_mode and p.color_mode.lower() == color_mode.lower()]

        if visual_style:
            results = [p for p in results
                       if any(visual_style.lower() in s.lower() for s in p.visual_style)]

        if query:
            query_lower = query.lower()
            scored = []
            for p in results:
                score = 0
                searchable = (
                    f"{p.name} {p.page_type} {' '.join(p.tags)} "
                    f"{' '.join(p.ux_patterns)} {' '.join(p.ui_elements)} "
                    f"{p.industry or ''} {p.behavioral_description or ''}"
                )
                searchable_lower = searchable.lower()
                for word in query_lower.split():
                    if word in searchable_lower:
                        score += 1
                if score > 0:
                    scored.append((score, p))
            scored.sort(key=lambda x: (-x[0], -(x[1].quality_score or 0)))
            results = [p for _, p in scored]
        else:
            # No query — rank by quality_score descending
            results = sorted(results, key=lambda p: -(p.quality_score or 0))

        return results[:limit]
