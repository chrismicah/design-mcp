"""Tests for DesignDatabase: load, save, search, add_batch, get by ID."""
import json
import pytest
from pathlib import Path

from database import DesignDatabase
from schema import DesignPattern


class TestDatabaseLoadSave:
    def test_load_empty_file(self, temp_db_path):
        db = DesignDatabase(temp_db_path)
        assert db.count() == 0

    def test_load_existing_data(self, populated_db, sample_patterns):
        assert populated_db.count() == len(sample_patterns)

    def test_save_creates_file(self, temp_db_path, curated_pattern):
        db = DesignDatabase(temp_db_path)
        db.add(curated_pattern)
        db.save()
        assert Path(temp_db_path).exists()
        with open(temp_db_path) as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["id"] == curated_pattern.id

    def test_roundtrip_preserves_data(self, temp_db_path, curated_pattern):
        db1 = DesignDatabase(temp_db_path)
        db1.add(curated_pattern)
        db1.save()
        db2 = DesignDatabase(temp_db_path)
        loaded = db2.get(curated_pattern.id)
        assert loaded is not None
        assert loaded.name == curated_pattern.name
        assert loaded.tags == curated_pattern.tags
        assert loaded.quality_score == curated_pattern.quality_score

    def test_creates_parent_directories(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c" / "patterns.json")
        db = DesignDatabase(nested)
        assert db.count() == 0
        assert Path(nested).parent.exists()


class TestDatabaseAddAndBatch:
    def test_add_single(self, empty_db, curated_pattern):
        empty_db.add(curated_pattern)
        assert empty_db.count() == 1

    def test_add_batch(self, empty_db, sample_patterns):
        empty_db.add_batch(sample_patterns)
        assert empty_db.count() == 3

    def test_add_batch_saves_to_disk(self, temp_db_path, sample_patterns):
        db = DesignDatabase(temp_db_path)
        db.add_batch(sample_patterns)
        # Verify file was written
        with open(temp_db_path) as f:
            data = json.load(f)
        assert len(data) == 3


class TestDatabaseGet:
    def test_get_existing(self, populated_db):
        result = populated_db.get("test-curated-001")
        assert result is not None
        assert result.name == "Stripe Dashboard"

    def test_get_missing(self, populated_db):
        result = populated_db.get("nonexistent-id")
        assert result is None

    def test_get_each_source(self, populated_db):
        assert populated_db.get("test-curated-001") is not None
        assert populated_db.get("test-dribbble-001") is not None
        assert populated_db.get("test-webui-001") is not None


class TestDatabaseSearch:
    def test_search_no_filters(self, populated_db):
        results = populated_db.search(limit=10)
        assert len(results) == 3

    def test_search_by_page_type(self, populated_db):
        results = populated_db.search(page_type="Dashboard")
        assert len(results) == 2
        assert all(r.page_type == "Dashboard" for r in results)

    def test_search_page_type_case_insensitive(self, populated_db):
        results = populated_db.search(page_type="dashboard")
        assert len(results) == 2

    def test_search_by_platform(self, populated_db):
        results = populated_db.search(platform="web")
        assert len(results) == 3

    def test_search_by_industry(self, populated_db):
        results = populated_db.search(industry="Fintech")
        assert len(results) == 1
        assert results[0].id == "test-curated-001"

    def test_search_industry_partial_match(self, populated_db):
        results = populated_db.search(industry="fin")
        assert len(results) == 1

    def test_search_by_color_mode(self, populated_db):
        results = populated_db.search(color_mode="dark")
        assert len(results) == 1
        assert results[0].id == "test-dribbble-001"

    def test_search_by_visual_style(self, populated_db):
        results = populated_db.search(visual_style="Minimal")
        assert len(results) == 2

    def test_search_by_query(self, populated_db):
        results = populated_db.search(query="stripe fintech")
        assert len(results) >= 1
        assert results[0].id == "test-curated-001"

    def test_search_query_no_match(self, populated_db):
        results = populated_db.search(query="xyznonexistent")
        assert len(results) == 0

    def test_search_limit(self, populated_db):
        results = populated_db.search(limit=1)
        assert len(results) == 1

    def test_search_combined_filters(self, populated_db):
        results = populated_db.search(page_type="Dashboard", color_mode="dark")
        assert len(results) == 1
        assert results[0].id == "test-dribbble-001"

    def test_search_no_results(self, populated_db):
        results = populated_db.search(page_type="404 Page")
        assert len(results) == 0

    def test_search_query_ranks_by_relevance(self, populated_db):
        """More keyword matches should rank higher."""
        results = populated_db.search(query="dashboard stripe fintech saas")
        assert len(results) >= 1
        # Curated pattern has more matching words
        assert results[0].id == "test-curated-001"
