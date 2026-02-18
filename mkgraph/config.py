"""Configuration management for mkgraph."""
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import os


CONFIG_DIR = Path.home() / ".mkgraph"
CONFIG_FILE = CONFIG_DIR / "config.json"


# Default entity types
DEFAULT_ENTITY_TYPES = ["person", "organization", "topic"]

# Default note template
DEFAULT_TEMPLATE = """---
sources: {sources}
---

# {name}

{description}

## Sources

{sources_list}
"""


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "openai"
    model: Optional[str] = None
    temperature: float = 0.3
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints


@dataclass
class TemplateConfig:
    """Note template configuration."""
    body: str = DEFAULT_TEMPLATE
    frontmatter_fields: list[str] = field(default_factory=lambda: ["sources"])


@dataclass
class EntityTypeConfig:
    """Configuration for a specific entity type."""
    directory: str = ""
    template: Optional[str] = None
    enabled: bool = True


@dataclass
class Config:
    """Main configuration for mkgraph."""
    # Entity types
    entity_types: list[str] = field(default_factory=lambda: DEFAULT_ENTITY_TYPES.copy())
    
    # Custom entity type configs
    entity_type_config: dict[str, EntityTypeConfig] = field(default_factory=dict)
    
    # LLM settings
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Template settings
    template: TemplateConfig = field(default_factory=TemplateConfig)
    
    # Output settings
    output_directories: dict[str, str] = field(default_factory=dict)
    
    # Strictness
    strictness: str = "medium"  # "high", "medium", "low"


def ensure_config_dir():
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_default_output_directories() -> dict[str, str]:
    """Get default output directory names."""
    return {
        "person": "People",
        "organization": "Organizations",
        "topic": "Topics",
    }


def load_config() -> Config:
    """Load configuration from file."""
    ensure_config_dir()
    
    if not CONFIG_FILE.exists():
        return Config()
    
    with open(CONFIG_FILE) as f:
        data = json.load(f)
    
    # Parse entity type config
    entity_type_config = {}
    for etype, et_config in data.get("entity_type_config", {}).items():
        entity_type_config[etype] = EntityTypeConfig(**et_config)
    
    # Parse LLM config
    llm_data = data.get("llm", {})
    llm_config = LLMConfig(**llm_data) if llm_data else LLMConfig()
    
    # Parse template config
    template_data = data.get("template", {})
    template_config = TemplateConfig(**template_data) if template_data else TemplateConfig()
    
    return Config(
        entity_types=data.get("entity_types", DEFAULT_ENTITY_TYPES.copy()),
        entity_type_config=entity_type_config,
        llm=llm_config,
        template=template_config,
        output_directories=data.get("output_directories", {}),
        strictness=data.get("strictness", "medium"),
    )


def save_config(config: Config):
    """Save configuration to file."""
    ensure_config_dir()
    
    # Convert to dict, handling dataclasses
    data = {
        "entity_types": config.entity_types,
        "entity_type_config": {
            k: {
                "directory": v.directory,
                "template": v.template,
                "enabled": v.enabled,
            }
            for k, v in config.entity_type_config.items()
        },
        "llm": {
            "provider": config.llm.provider,
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "api_key": config.llm.api_key,
            "base_url": config.llm.base_url,
        },
        "template": {
            "body": config.template.body,
            "frontmatter_fields": config.template.frontmatter_fields,
        },
        "output_directories": config.output_directories,
        "strictness": config.strictness,
    }
    
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_entity_directory(entity_type: str, config: Optional[Config] = None) -> str:
    """Get output directory for an entity type."""
    if config and config.output_directories.get(entity_type):
        return config.output_directories[entity_type]
    
    defaults = get_default_output_directories()
    return defaults.get(entity_type, entity_type.title() + "s")


def get_entity_template(entity_type: str, config: Optional[Config] = None) -> str:
    """Get template for an entity type."""
    if config and config.entity_type_config.get(entity_type):
        custom = config.entity_type_config[entity_type]
        if custom.template:
            return custom.template
    
    if config and config.template.body:
        return config.template.body
    
    return DEFAULT_TEMPLATE


def is_entity_enabled(entity_type: str, config: Optional[Config] = None) -> bool:
    """Check if an entity type is enabled."""
    if config and config.entity_type_config.get(entity_type):
        return config.entity_type_config[entity_type].enabled
    
    if config:
        return entity_type in config.entity_types
    
    return entity_type in DEFAULT_ENTITY_TYPES


def reset_config():
    """Reset config to defaults."""
    ensure_config_dir()
    
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
