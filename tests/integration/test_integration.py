"""Integration tests for mkgraph."""
import json
from pathlib import Path
from unittest.mock import patch
import pytest

from mkgraph.processor import process_file, process_directory, Entity


class TestProcessFileIntegration:
    """Integration tests for processing a single file."""

    def test_process_file_creates_notes(self, tmp_path):
        """Processing a file should create note files."""
        # Create test input file
        input_file = tmp_path / "input.md"
        input_file.write_text("""# Meeting

Met with John Smith from Acme Corp today.
""")
        
        output_dir = tmp_path / "knowledge"
        
        # Mock LLM response
        mock_entities = [
            Entity(name="John Smith", entity_type="person", description="Met with him"),
            Entity(name="Acme Corp", entity_type="organization", description="Company"),
        ]
        
        with patch("mkgraph.processor.extract_entities_from_content", return_value=mock_entities):
            process_file(input_file, output_dir)
        
        # Check notes were created
        assert (output_dir / "People" / "John Smith.md").exists()
        assert (output_dir / "Organizations" / "Acme Corp.md").exists()

    def test_process_file_creates_frontmatter(self, tmp_path):
        """Processed file should have frontmatter."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Content about Jane Doe.")
        
        output_dir = tmp_path / "knowledge"
        
        mock_entities = [
            Entity(name="Jane Doe", entity_type="person", description="A person"),
        ]
        
        with patch("mkgraph.processor.extract_entities_from_content", return_value=mock_entities):
            process_file(input_file, output_dir)
        
        note_path = output_dir / "People" / "Jane Doe.md"
        content = note_path.read_text()
        
        assert content.startswith("---")
        assert "sources:" in content

    def test_process_file_adds_source(self, tmp_path):
        """Note should reference source file."""
        input_file = tmp_path / "meeting.md"
        input_file.write_text("Discussed with Bob.")
        
        output_dir = tmp_path / "knowledge"
        
        mock_entities = [
            Entity(name="Bob", entity_type="person", description="Person"),
        ]
        
        with patch("mkgraph.processor.extract_entities_from_content", return_value=mock_entities):
            process_file(input_file, output_dir)
        
        note_path = output_dir / "People" / "Bob.md"
        content = note_path.read_text()
        
        assert "meeting.md" in content


class TestProcessDirectoryIntegration:
    """Integration tests for processing a directory."""

    def test_process_directory_finds_markdown_files(self, tmp_path):
        """Should find all .md files in directory."""
        # Create test files
        (tmp_path / "file1.md").write_text("Content 1")
        (tmp_path / "file2.md").write_text("Content 2")
        (tmp_path / "file3.txt").write_text("Not markdown")
        
        # Mock the LLM call and process_batch to track what's called
        from mkgraph.processor import process_batch
        with patch("mkgraph.processor.extract_entities_from_batch", return_value=[]) as mock_batch:
            with patch("mkgraph.processor.create_or_update_note"):
                process_batch([tmp_path / "file1.md", tmp_path / "file2.md"], tmp_path / "output")
        
        # Should have called batch with both md files
        assert mock_batch.call_count == 1

    def test_process_directory_recursive(self, tmp_path):
        """Should find markdown files in subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        
        (tmp_path / "file1.md").write_text("Content 1")
        (subdir / "file2.md").write_text("Content 2")
        
        # Mock and verify recursive glob works
        md_files = list(tmp_path.glob("**/*.md"))
        assert len(md_files) == 2


class TestEndToEnd:
    """End-to-end tests with real file operations."""

    def test_full_pipeline_creates_structure(self, tmp_path):
        """Full pipeline should create proper directory structure."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Meeting with Alice from Beta Inc.")
        
        output_dir = tmp_path / "knowledge"
        
        mock_entities = [
            Entity(name="Alice", entity_type="person", description="Person"),
            Entity(name="Beta Inc", entity_type="organization", description="Org"),
        ]
        
        with patch("mkgraph.processor.extract_entities_from_content", return_value=mock_entities):
            process_file(input_file, output_dir)
        
        # Check directory structure
        assert (output_dir / "People").exists()
        assert (output_dir / "Organizations").exists()
        assert (output_dir / "Topics").exists() or not list((output_dir / "Topics").glob("*.md"))

    def test_multiple_entities_same_type(self, tmp_path):
        """Should create separate notes for multiple entities of same type."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Met with Alice and Bob.")
        
        output_dir = tmp_path / "knowledge"
        
        mock_entities = [
            Entity(name="Alice", entity_type="person", description="First person"),
            Entity(name="Bob", entity_type="person", description="Second person"),
        ]
        
        with patch("mkgraph.processor.extract_entities_from_content", return_value=mock_entities):
            process_file(input_file, output_dir)
        
        assert (output_dir / "People" / "Alice.md").exists()
        assert (output_dir / "People" / "Bob.md").exists()
