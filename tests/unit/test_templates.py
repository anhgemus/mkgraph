"""Unit tests for prompt templates."""
import pytest

from mkgraph.templates import get_extraction_prompt


class TestGetExtractionPrompt:
    """Tests for get_extraction_prompt function."""

    def test_prompt_contains_entity_types(self):
        """Prompt should list all entity types."""
        prompt = get_extraction_prompt("test content")
        
        assert "person" in prompt.lower()
        assert "organization" in prompt.lower()
        assert "topic" in prompt.lower()

    def test_prompt_contains_content(self):
        """Prompt should include the input content."""
        test_content = "This is test content about John Doe."
        
        prompt = get_extraction_prompt(test_content)
        
        assert test_content in prompt

    def test_prompt_requests_json(self):
        """Prompt should ask for JSON output."""
        prompt = get_extraction_prompt("test")
        
        assert "json" in prompt.lower()

    def test_prompt_not_empty(self):
        """Prompt should not be empty."""
        prompt = get_extraction_prompt("test")
        
        assert len(prompt) > 0

    def test_prompt_contains_format_example(self):
        """Prompt should include output format example."""
        prompt = get_extraction_prompt("test")
        
        assert "```json" in prompt
