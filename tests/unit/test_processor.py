"""Unit tests for entity extraction and processing."""
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from mkgraph.processor import (
    compute_file_hash,
    extract_entities_from_content,
    get_notes_dir,
    Entity,
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash_consistency(self, tmp_path):
        """Same content should produce same hash."""
        file = tmp_path / "test.txt"
        file.write_text("hello world")
        
        hash1 = compute_file_hash(file)
        hash2 = compute_file_hash(file)
        
        assert hash1 == hash2

    def test_compute_hash_different_content(self, tmp_path):
        """Different content should produce different hashes."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("hello world")
        file2.write_text("hello world!")
        
        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)
        
        assert hash1 != hash2


class TestExtractEntities:
    """Tests for entity extraction parsing."""

    def test_parse_valid_json_response(self):
        """Should parse valid JSON response from LLM."""
        json_response = json.dumps([
            {"name": "John Doe", "type": "person", "description": "A person"},
            {"name": "Acme Inc", "type": "organization", "description": "A company"},
        ])
        
        # Mock the LLM call
        with patch("mkgraph.processor.call_llm", return_value=json_response):
            entities = extract_entities_from_content("test content")
        
        assert len(entities) == 2
        assert entities[0].name == "John Doe"
        assert entities[0].entity_type == "person"
        assert entities[1].name == "Acme Inc"
        assert entities[1].entity_type == "organization"

    def test_extract_invalid_json(self):
        """Should handle invalid JSON gracefully."""
        with patch("mkgraph.processor.call_llm", return_value="not valid json"):
            entities = extract_entities_from_content("test content")
        
        assert entities == []

    def test_extract_json_in_markdown(self):
        """Should extract JSON from markdown code blocks."""
        markdown_response = '''```json
[
  {"name": "Test", "type": "person", "description": "Test person"}
]
```'''
        
        with patch("mkgraph.processor.call_llm", return_value=markdown_response):
            entities = extract_entities_from_content("test content")
        
        assert len(entities) == 1
        assert entities[0].name == "Test"

    def test_filter_invalid_entity_types(self):
        """Should filter out invalid entity types."""
        json_response = json.dumps([
            {"name": "Valid Person", "type": "person", "description": "A person"},
            {"name": "Invalid Type", "type": "invalid", "description": "Should be filtered"},
            {"name": "Another Valid", "type": "topic", "description": "A topic"},
        ])
        
        with patch("mkgraph.processor.call_llm", return_value=json_response):
            entities = extract_entities_from_content("test content")
        
        assert len(entities) == 2
        assert all(e.entity_type in ["person", "organization", "topic"] for e in entities)


class TestGetNotesDir:
    """Tests for get_notes_dir function."""

    def test_get_notes_dir_structure(self, tmp_path):
        """Should return correct directory paths."""
        output = tmp_path / "knowledge"
        dirs = get_notes_dir(output)
        
        assert dirs["people"] == output / "People"
        assert dirs["organizations"] == output / "Organizations"
        assert dirs["topics"] == output / "Topics"


class TestEntity:
    """Tests for Entity dataclass."""

    def test_entity_creation(self):
        """Should create entity with correct attributes."""
        entity = Entity(
            name="Test Entity",
            entity_type="person",
            description="A test person",
            sources=["source1.md", "source2.md"]
        )
        
        assert entity.name == "Test Entity"
        assert entity.entity_type == "person"
        assert entity.description == "A test person"
        assert entity.sources == ["source1.md", "source2.md"]

    def test_entity_default_sources(self):
        """Should have empty sources by default."""
        entity = Entity(name="Test", entity_type="topic")
        
        assert entity.sources == []


class TestMergeEntities:
    """Tests for merge_entities function."""

    def test_merge_same_entity(self):
        """Should merge entities with same name and type."""
        from mkgraph.processor import merge_entities
        
        entities1 = [
            Entity(name="John", entity_type="person", description="First", sources=["file1.md"]),
        ]
        entities2 = [
            Entity(name="John", entity_type="person", description="Second", sources=["file2.md"]),
        ]
        
        merged = merge_entities([entities1, entities2])
        
        assert len(merged) == 1
        assert len(merged[0].sources) == 2
        assert "file1.md" in merged[0].sources
        assert "file2.md" in merged[0].sources

    def test_merge_different_entities(self):
        """Should keep different entities separate."""
        from mkgraph.processor import merge_entities
        
        entities1 = [
            Entity(name="John", entity_type="person", description="Person", sources=["file1.md"]),
        ]
        entities2 = [
            Entity(name="Acme", entity_type="organization", description="Org", sources=["file2.md"]),
        ]
        
        merged = merge_entities([entities1, entities2])
        
        assert len(merged) == 2

    def test_merge_keeps_longer_description(self):
        """Should keep longer description when merging."""
        from mkgraph.processor import merge_entities
        
        entities1 = [
            Entity(name="John", entity_type="person", description="Short", sources=["file1.md"]),
        ]
        entities2 = [
            Entity(name="John", entity_type="person", description="Much longer description here", sources=["file2.md"]),
        ]
        
        merged = merge_entities([entities1, entities2])
        
        assert merged[0].description == "Much longer description here"

    def test_merge_case_insensitive(self):
        """Should merge entities regardless of case."""
        from mkgraph.processor import merge_entities
        
        entities1 = [
            Entity(name="John Smith", entity_type="person", description="Person", sources=["file1.md"]),
        ]
        entities2 = [
            Entity(name="john smith", entity_type="person", description="Same", sources=["file2.md"]),
        ]
        
        merged = merge_entities([entities1, entities2])
        
        assert len(merged) == 1
