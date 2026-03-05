"""Tests for DesignPattern schema validation."""
import pytest
from pydantic import ValidationError

from schema import DesignPattern, Platform, LayoutType


class TestRequiredFields:
    def test_minimal_valid_pattern(self):
        p = DesignPattern(
            id="test-1",
            name="Test Pattern",
            source="curated",
            source_url="https://example.com",
            page_type="Dashboard",
        )
        assert p.id == "test-1"
        assert p.platform == Platform.WEB  # default

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                name="Test", source="curated",
                source_url="https://example.com", page_type="Dashboard"
            )

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="test-1", source="curated",
                source_url="https://example.com", page_type="Dashboard"
            )

    def test_missing_source_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="test-1", name="Test",
                source_url="https://example.com", page_type="Dashboard"
            )

    def test_missing_source_url_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="test-1", name="Test",
                source="curated", page_type="Dashboard"
            )

    def test_missing_page_type_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="test-1", name="Test",
                source="curated", source_url="https://example.com"
            )


class TestOptionalFields:
    def test_defaults_are_none_or_empty(self):
        p = DesignPattern(
            id="t", name="t", source="s",
            source_url="https://x.com", page_type="Landing Page"
        )
        assert p.image_url is None
        assert p.layout_type is None
        assert p.layout_notes is None
        assert p.color_mode is None
        assert p.behavioral_description is None
        assert p.accessibility_notes is None
        assert p.semantic_tokens is None
        assert p.quality_score is None
        assert p.ux_patterns == []
        assert p.ui_elements == []
        assert p.visual_style == []
        assert p.primary_colors == []
        assert p.component_hints == []
        assert p.tags == []

    def test_all_optional_fields_populated(self, curated_pattern_data):
        p = DesignPattern(**curated_pattern_data)
        assert p.image_url is not None
        assert p.layout_type == LayoutType.SIDEBAR_MAIN
        assert p.quality_score == 9.5
        assert len(p.tags) > 0


class TestEnumValidation:
    def test_valid_platform_values(self):
        for val in ["web", "ios", "android"]:
            p = DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                platform=val
            )
            assert p.platform.value == val

    def test_invalid_platform_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                platform="windows"
            )

    def test_valid_layout_types(self):
        for lt in LayoutType:
            p = DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                layout_type=lt.value
            )
            assert p.layout_type == lt

    def test_invalid_layout_type_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                layout_type="table_layout"
            )


class TestQualityScoreBounds:
    def test_quality_score_zero(self):
        p = DesignPattern(
            id="t", name="t", source="s",
            source_url="https://x.com", page_type="P",
            quality_score=0.0
        )
        assert p.quality_score == 0.0

    def test_quality_score_ten(self):
        p = DesignPattern(
            id="t", name="t", source="s",
            source_url="https://x.com", page_type="P",
            quality_score=10.0
        )
        assert p.quality_score == 10.0

    def test_quality_score_negative_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                quality_score=-1.0
            )

    def test_quality_score_above_ten_raises(self):
        with pytest.raises(ValidationError):
            DesignPattern(
                id="t", name="t", source="s",
                source_url="https://x.com", page_type="P",
                quality_score=10.1
            )


class TestModelDump:
    def test_model_dump_roundtrip(self, curated_pattern_data):
        p = DesignPattern(**curated_pattern_data)
        dumped = p.model_dump()
        p2 = DesignPattern(**dumped)
        assert p.id == p2.id
        assert p.tags == p2.tags
        assert p.quality_score == p2.quality_score

    def test_exclude_none(self):
        p = DesignPattern(
            id="t", name="t", source="s",
            source_url="https://x.com", page_type="P"
        )
        dumped = p.model_dump(exclude_none=True)
        assert "image_url" not in dumped
        assert "layout_type" not in dumped
