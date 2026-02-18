"""Unit tests for config module."""
import json
from pathlib import Path
import pytest

from mkgraph.config import (
    Config,
    LLMConfig,
    TemplateConfig,
    EntityTypeConfig,
    load_config,
    save_config,
    get_entity_directory,
    get_entity_template,
    is_entity_enabled,
    get_default_output_directories,
    CONFIG_FILE,
)


@pytest.fixture
def tmp_config_file(tmp_path, monkeypatch):
    """Create a temporary config file."""
    config_file = tmp_path / "config.json"
    monkeypatch.setattr("mkgraph.config.CONFIG_FILE", config_file)
    return config_file


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_defaults(self):
        """Should have correct defaults."""
        cfg = LLMConfig()
        
        assert cfg.provider == "openai"
        assert cfg.model is None
        assert cfg.temperature == 0.3


class TestConfig:
    """Tests for Config."""

    def test_defaults(self):
        """Should have correct defaults."""
        cfg = Config()
        
        assert cfg.entity_types == ["person", "organization", "topic"]
        assert cfg.llm.provider == "openai"
        assert cfg.strictness == "medium"


class TestLoadSaveConfig:
    """Tests for load and save config."""

    def test_load_empty_config(self, tmp_config_file):
        """Should return defaults when no file exists."""
        cfg = load_config()
        
        assert cfg.entity_types == ["person", "organization", "topic"]

    def test_save_and_load_config(self, tmp_config_file):
        """Should save and load config correctly."""
        cfg = Config(
            entity_types=["person", "organization"],
            strictness="high"
        )
        cfg.llm.provider = "ollama"
        
        save_config(cfg)
        
        loaded = load_config()
        
        assert loaded.entity_types == ["person", "organization"]
        assert loaded.strictness == "high"
        assert loaded.llm.provider == "ollama"


class TestGetEntityDirectory:
    """Tests for get_entity_directory."""

    def test_default_directories(self):
        """Should return default directories."""
        assert get_entity_directory("person") == "People"
        assert get_entity_directory("organization") == "Organizations"
        assert get_entity_directory("topic") == "Topics"

    def test_custom_directories(self, tmp_config_file):
        """Should use custom directories from config."""
        cfg = Config()
        cfg.output_directories = {"person": "Contacts"}
        
        assert get_entity_directory("person", cfg) == "Contacts"
        # Others should still use defaults
        assert get_entity_directory("organization", cfg) == "Organizations"


class TestIsEntityEnabled:
    """Tests for is_entity_enabled."""

    def test_default_enabled(self):
        """Default types should be enabled."""
        assert is_entity_enabled("person") is True
        assert is_entity_enabled("organization") is True
        assert is_entity_enabled("topic") is True

    def test_custom_disabled(self, tmp_config_file):
        """Should respect disabled setting."""
        cfg = Config()
        cfg.entity_type_config["person"] = EntityTypeConfig(enabled=False)
        
        assert is_entity_enabled("person", cfg) is False
        assert is_entity_enabled("organization", cfg) is True


class TestGetDefaultOutputDirectories:
    """Tests for get_default_output_directories."""

    def test_returns_dict(self):
        """Should return a dictionary."""
        result = get_default_output_directories()
        
        assert isinstance(result, dict)
        assert "person" in result
        assert "organization" in result
        assert "topic" in result
