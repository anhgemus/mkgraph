"""Core processing logic for knowledge graph creation."""
import json
import os
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal

from mkgraph.llm import call_llm
from mkgraph.templates import get_extraction_prompt


@dataclass
class Entity:
    """Represents an extracted entity."""
    name: str
    entity_type: Literal["person", "organization", "topic"]
    description: str = ""
    sources: list[str] = field(default_factory=list)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def extract_entities_from_content(content: str, llm: str = "openai", model: str | None = None) -> list[Entity]:
    """Call LLM to extract entities from markdown content."""
    prompt = get_extraction_prompt(content)
    
    response = call_llm(prompt, llm=llm, model=model)
    
    # Parse JSON response
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            print(f"Warning: Could not parse LLM response as JSON: {response[:200]}")
            return []
    
    entities = []
    for item in data:
        entity_type = item.get("type", "").lower()
        if entity_type not in ["person", "organization", "topic"]:
            continue
        
        entities.append(Entity(
            name=item.get("name", ""),
            entity_type=entity_type,
            description=item.get("description", ""),
        ))
    
    return entities


def get_notes_dir(output_dir: Path) -> dict[str, Path]:
    """Get note directory paths."""
    return {
        "people": output_dir / "People",
        "organizations": output_dir / "Organizations",
        "topics": output_dir / "Topics",
    }


def create_note(entity: Entity, output_dir: Path, source_file: str):
    """Create or update a note for an entity."""
    notes_dir = get_notes_dir(output_dir)
    
    if entity.entity_type == "person":
        note_dir = notes_dir["people"]
    elif entity.entity_type == "organization":
        note_dir = notes_dir["organizations"]
    else:
        note_dir = notes_dir["topics"]
    
    # Create directory if needed
    note_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize name for filename
    filename = entity.name.replace("/", "-").replace("\\", "-")
    note_path = note_dir / f"{filename}.md"
    
    # Build note content
    frontmatter = f"""---
created: {json.dumps(entity.sources)}
sources: {json.dumps([source_file])}
---

# {entity.name}

"""
    
    # Check if note exists
    if note_path.exists():
        with open(note_path) as f:
            existing = f.read()
        
        # Check if source already added
        if source_file in existing:
            return  # Already linked
        
        # Append to existing note
        new_content = existing.rstrip() + f"\n\n## Sources\n\n- {source_file}\n"
        
        # Add description if new
        if entity.description and entity.description not in existing:
            # Insert description after frontmatter if not present
            lines = existing.split("\n")
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip() == "---" and i > 0:
                    insert_idx = i + 1
                    break
            lines.insert(insert_idx, f"\n{entity.description}\n")
            new_content = "\n".join(lines)
        
        with open(note_path, "w") as f:
            f.write(new_content)
    else:
        # Create new note
        content = frontmatter
        if entity.description:
            content += f"{entity.description}\n"
        content += f"\n## Sources\n\n- {source_file}\n"
        
        with open(note_path, "w") as f:
            f.write(content)


def process_file(
    file_path: Path,
    output_dir: Path,
    llm: str = "openai",
    model: str | None = None,
    verbose: bool = False
):
    """Process a single markdown file and extract entities."""
    if verbose:
        print(f"Reading: {file_path}")
    
    with open(file_path) as f:
        content = f.read()
    
    if verbose:
        print(f"Extracting entities via {llm}...")
    
    entities = extract_entities_from_content(content, llm=llm, model=model)
    
    if verbose:
        print(f"Found {len(entities)} entities")
    
    for entity in entities:
        entity.sources.append(str(file_path))
        create_note(entity, output_dir, str(file_path))
        if verbose:
            print(f"  - {entity.entity_type}: {entity.name}")
    
    return entities


def process_directory(
    input_dir: Path,
    output_dir: Path,
    llm: str = "openai",
    model: str | None = None,
    verbose: bool = False
):
    """Process all markdown files in a directory."""
    md_files = list(input_dir.glob("**/*.md"))
    
    if verbose:
        print(f"Found {len(md_files)} markdown files")
    
    for md_file in md_files:
        process_file(md_file, output_dir, llm=llm, model=model, verbose=verbose)
