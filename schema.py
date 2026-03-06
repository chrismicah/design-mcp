from pydantic import BaseModel, Field
from typing import Optional, Union
from enum import Enum


class Platform(str, Enum):
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"


class LayoutType(str, Enum):
    """Research finding: Explicit layout type prevents brittle absolute positioning."""
    FLEXBOX = "flexbox"
    CSS_GRID = "css_grid"
    BENTO_GRID = "bento_grid"
    SINGLE_COLUMN = "single_column"
    SIDEBAR_MAIN = "sidebar_main"
    SIDEBAR_DETAIL = "sidebar_detail"
    SPLIT_SCREEN = "split_screen"
    MASONRY = "masonry"
    STACKED = "stacked"
    FULL_BLEED = "full_bleed"
    CARD_GRID = "card_grid"
    DASHBOARD_PANELS = "dashboard_panels"
    HOLY_GRAIL = "holy_grail"
    STICKY_HEADER = "sticky_header"
    EDITORIAL = "editorial"


class DesignPattern(BaseModel):
    """
    A single design pattern/screen in the database.
    Schema fields are chosen based on empirical research into what
    metadata most improves LLM UI generation quality.
    """

    # === IDENTITY ===
    id: str = Field(description="Unique identifier")
    name: str = Field(description="Descriptive name, e.g. 'Stripe Dashboard Empty State'")
    source: str = Field(description="Origin platform: dribbble, awwwards, webui-7kbal, etc.")
    source_url: str = Field(description="Original URL for reference")
    image_url: Optional[str] = Field(default=None, description="Screenshot URL if available")

    # === TAXONOMY (High impact — acts as semantic anchor for the LLM) ===
    page_type: str = Field(description="E.g. 'Dashboard', 'Pricing Table', '404 Page', 'Onboarding', 'Settings'")
    ux_patterns: list[str] = Field(
        default_factory=list,
        description="E.g. ['Skeleton Loading', 'Progressive Disclosure', 'Multi-Step Form', 'Empty State']"
    )
    ui_elements: list[str] = Field(
        default_factory=list,
        description="E.g. ['Accordion', 'Avatar', 'Badge', 'Toggle', 'Date Picker', 'Modal']"
    )
    industry: Optional[str] = Field(default=None, description="E.g. 'Fintech', 'Health', 'E-Commerce', 'SaaS', 'Education'")

    # === LAYOUT (High impact — prevents absolute positioning hallucination) ===
    layout_type: Optional[LayoutType] = Field(
        default=None,
        description="Primary layout strategy. Research shows this alone significantly improves structural output."
    )
    layout_notes: Optional[str] = Field(
        default=None,
        description="Brief description: 'Sidebar 280px fixed, main content scrollable with 24px gap grid'"
    )

    # === VISUAL STYLE (Medium impact — useful for global styling) ===
    platform: Platform = Field(default=Platform.WEB)
    color_mode: Optional[str] = Field(default=None, description="'light', 'dark', or 'auto'")
    visual_style: list[str] = Field(
        default_factory=list,
        description="E.g. ['Glassmorphism', 'Minimal', 'Brutalist', 'Neubrutalism', 'Flat', 'Skeuomorphic']"
    )
    primary_colors: list[str] = Field(
        default_factory=list,
        description="Dominant hex colors observed: ['#1a1a2e', '#e94560', '#0f3460']"
    )

    # === BEHAVIORAL CONTEXT (High impact — gives the LLM interaction logic) ===
    behavioral_description: Optional[str] = Field(
        default=None,
        description=(
            "How this pattern BEHAVES, not just looks. E.g.: "
            "'Empty state educates user on feature value, shows illustration, "
            "provides single prominent CTA to create first item. "
            "Loading shows skeleton matching final layout. "
            "Error state offers retry with preserved form data.'"
        )
    )

    # === COMPONENT PROPS (High impact — prevents hallucinated component structure) ===
    component_hints: list[dict] = Field(
        default_factory=list,
        description=(
            "Known component structures. E.g.: "
            "[{'name': 'PricingCard', 'props': ['tier', 'price', 'features', 'cta_text', 'is_popular']}]"
        )
    )

    # === ACCESSIBILITY (High impact — 60% reduction in inaccessibility when provided) ===
    accessibility_notes: Optional[str] = Field(
        default=None,
        description=(
            "E.g. 'Requires ARIA landmarks for nav, main, complementary. "
            "Color contrast must meet WCAG AA (4.5:1 for text). "
            "All interactive elements need visible focus indicators.'"
        )
    )

    # === SEMANTIC TOKENS (High impact — avoids magic numbers) ===
    semantic_tokens: Optional[Union[dict, str]] = Field(
        default=None,
        description=(
            "Tier 2 semantic tokens observed or inferred. E.g.: "
            "{'color-background-primary': '#1a1a2e', 'spacing-section': '48px', "
            "'border-radius-card': '12px', 'font-heading': 'Inter'}"
        )
    )

    # === META ===
    quality_score: Optional[float] = Field(
        default=None, ge=0, le=10,
        description="Subjective quality rating. Used for search ranking."
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Freeform tags for search: ['saas', 'dark-mode', 'illustration', 'startup']"
    )
