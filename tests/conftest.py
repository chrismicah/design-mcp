import pytest
import json
import tempfile
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from schema import DesignPattern, Platform, LayoutType
from database import DesignDatabase


@pytest.fixture
def curated_pattern_data():
    """A fully-populated curated pattern (high quality)."""
    return {
        "id": "test-curated-001",
        "name": "Stripe Dashboard",
        "source": "curated",
        "source_url": "https://dashboard.stripe.com",
        "image_url": "https://example.com/stripe.png",
        "page_type": "Dashboard",
        "ux_patterns": ["Skeleton Loading", "Empty State", "Search with Filters"],
        "ui_elements": ["Navigation Bar", "Sidebar", "Card", "Data Table", "Badge", "Button"],
        "industry": "Fintech",
        "layout_type": "sidebar_main",
        "layout_notes": "Fixed 240px sidebar, main content area with 24px grid gap",
        "platform": "web",
        "color_mode": "light",
        "visual_style": ["Minimal", "Corporate"],
        "primary_colors": ["#635bff", "#0a2540"],
        "behavioral_description": "Dashboard shows overview metrics in cards at top.",
        "component_hints": [{"name": "MetricCard", "props": ["title", "value"]}],
        "accessibility_notes": "ARIA landmarks for nav, main. WCAG AA compliant.",
        "semantic_tokens": {"color-bg-primary": "#f6f9fc", "spacing-section": "32px"},
        "quality_score": 9.5,
        "tags": ["fintech", "dashboard", "stripe", "saas"],
    }


@pytest.fixture
def dribbble_pattern_data():
    """A dribbble pattern (medium quality, less metadata)."""
    return {
        "id": "test-dribbble-001",
        "name": "AI Dashboard Dark Mode",
        "source": "dribbble",
        "source_url": "https://dribbble.com/shots/12345",
        "page_type": "Dashboard",
        "ux_patterns": [],
        "ui_elements": [],
        "industry": "SaaS",
        "color_mode": "dark",
        "visual_style": ["Minimal", "Futuristic"],
        "tags": ["dashboard", "dark-mode", "dribbble"],
    }


@pytest.fixture
def webui_pattern_data():
    """A webui-7kbal pattern (sparse metadata)."""
    return {
        "id": "test-webui-001",
        "name": "MIT License Page",
        "source": "webui-7kbal",
        "source_url": "http://example.com/license",
        "page_type": "Landing Page",
        "ux_patterns": [],
        "ui_elements": [],
        "industry": "Developer Tools",
        "tags": ["webui-7kbal"],
    }


@pytest.fixture
def curated_pattern(curated_pattern_data):
    return DesignPattern(**curated_pattern_data)


@pytest.fixture
def dribbble_pattern(dribbble_pattern_data):
    return DesignPattern(**dribbble_pattern_data)


@pytest.fixture
def webui_pattern(webui_pattern_data):
    return DesignPattern(**webui_pattern_data)


@pytest.fixture
def sample_patterns(curated_pattern, dribbble_pattern, webui_pattern):
    """List of 3 sample patterns of different sources."""
    return [curated_pattern, dribbble_pattern, webui_pattern]


@pytest.fixture
def temp_db_path(tmp_path):
    """Path for a temporary database file."""
    return str(tmp_path / "test_patterns.json")


@pytest.fixture
def empty_db(temp_db_path):
    """An empty DesignDatabase."""
    return DesignDatabase(temp_db_path)


@pytest.fixture
def populated_db(temp_db_path, sample_patterns):
    """A DesignDatabase pre-loaded with sample patterns."""
    # Write sample data to file first
    data = [p.model_dump() for p in sample_patterns]
    path = Path(temp_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)
    return DesignDatabase(temp_db_path)
