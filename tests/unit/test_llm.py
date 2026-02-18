"""Unit tests for LLM module."""
import os
from unittest.mock import patch, MagicMock
import pytest

from mkgraph.llm import call_llm, get_openai_client, get_anthropic_client


class TestCallLLM:
    """Tests for call_llm function."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("mkgraph.llm.OpenAI")
    def test_call_openai(self, mock_openai):
        """Should call OpenAI correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="test response"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = call_llm("test prompt", llm="openai")
        
        assert result == "test response"
        mock_client.chat.completions.create.assert_called_once()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("mkgraph.llm.Anthropic")
    def test_call_anthropic(self, mock_anthropic):
        """Should call Anthropic correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test response")]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        result = call_llm("test prompt", llm="anthropic")
        
        assert result == "test response"
        mock_client.messages.create.assert_called_once()

    @patch("mkgraph.llm.requests.post")
    def test_call_ollama(self, mock_post):
        """Should call Ollama correctly."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"response": "test response"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        
        result = call_llm("test prompt", llm="ollama", model="llama3.2")
        
        assert result == "test response"
        mock_post.assert_called_once()

    def test_unknown_provider(self):
        """Should raise error for unknown provider."""
        with pytest.raises(ValueError, match="Unknown LLM provider"):
            call_llm("test prompt", llm="unknown")


class TestGetOpenAIClient:
    """Tests for get_openai_client function."""

    def test_missing_api_key(self):
        """Should raise error if API key not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
                get_openai_client()

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("mkgraph.llm.OpenAI")
    def test_client_creation(self, mock_openai):
        """Should create client with correct API key."""
        get_openai_client()
        
        mock_openai.assert_called_once_with(api_key="test-key")


class TestGetAnthropicClient:
    """Tests for get_anthropic_client function."""

    def test_missing_api_key(self):
        """Should raise error if API key not set."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
                get_anthropic_client()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("mkgraph.llm.Anthropic")
    def test_client_creation(self, mock_anthropic):
        """Should create client with correct API key."""
        get_anthropic_client()
        
        mock_anthropic.assert_called_once_with(api_key="test-key")
