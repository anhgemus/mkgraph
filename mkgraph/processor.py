"""Core processing logic for knowledge graph creation."""
import json
import os
import hashlib
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal, Optional

from mkgraph.llm import call_llm
from mkgraph.templates import get_extraction_prompt, get_batch_extraction_prompt
from mkgraph.state import load_state, save_state, mark_file_processed, get_unprocessed_files
from mkgraph import config as config_module


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


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for matching."""
    return name.lower().strip().replace("_", " ").replace("-", " ")


def extract_entities_from_content(content: str, llm: str = "openai", model: str | None = None) -> list[Entity]:
    """Call LLM to extract entities from markdown content."""
    prompt = get_extraction_prompt(content)
    
    response = call_llm(prompt, llm=llm, model=model)
    
    return parse_entities_response(response, [])


def extract_entities_from_batch(
    files: list[tuple[str, str]],  # list of (path, content)
    llm: str = "openai",
    model: str | None = None
) -> list[Entity]:
    """Extract entities from multiple files in a single LLM call."""
    prompt = get_batch_extraction_prompt(files)
    
    response = call_llm(prompt, llm=llm, model=model)
    
    paths = [f[0] for f in files]
    return parse_entities_response(response, paths)


def parse_entities_response(response: str, fallback_sources: list[str]) -> list[Entity]:
    """Parse JSON response from LLM into Entity objects."""
    # Parse JSON response
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                print(f"Warning: Could not parse LLM response as JSON: {response[:200]}")
                return []
        else:
            print(f"Warning: Could not parse LLM response as JSON: {response[:200]}")
            return []
    
    entities = []
    for item in data:
        entity_type = item.get("type", "").lower()
        if entity_type not in ["person", "organization", "topic"]:
            continue
        
        name = item.get("name", "").strip()
        if not name:
            continue
        
        # Get source - prefer source field from LLM, fallback to provided sources
        source = item.get("source", "")
        if not source and fallback_sources:
            source = fallback_sources[0] if fallback_sources else ""
        
        entities.append(Entity(
            name=name,
            entity_type=entity_type,
            description=item.get("description", ""),
            sources=[source] if source else []
        ))
    
    return entities


def merge_entities(entity_lists: list[list[Entity]]) -> list[Entity]:
    """Merge entities from multiple sources, combining duplicates."""
    merged: dict[str, Entity] = {}
    
    for entities in entity_lists:
        for entity in entities:
            # Use normalized name as key
            key = f"{normalize_entity_name(entity.name)}:{entity.entity_type}"
            
            if key in merged:
                # Merge: add sources, combine descriptions
                existing = merged[key]
                
                # Add new sources
                for source in entity.sources:
                    if source not in existing.sources:
                        existing.sources.append(source)
                
                # Merge descriptions (prefer longer)
                if entity.description and len(entity.description) > len(existing.description):
                    existing.description = entity.description
            else:
                # Add new entity
                merged[key] = entity
    
    return list(merged.values())


def get_notes_dir(output_dir: Path, config: Optional[config_module.Config] = None) -> dict[str, Path]:
    """Get note directory paths."""
    if config is None:
        config = config_module.load_config()
    
    defaults = config_module.get_default_output_directories()
    
    return {
        "people": output_dir / config.output_directories.get("person", defaults.get("person", "People")),
        "organizations": output_dir / config.output_directories.get("organization", defaults.get("organization", "Organizations")),
        "topics": output_dir / config.output_directories.get("topic", defaults.get("topic", "Topics")),
    }


def sanitize_filename(name: str) -> str:
    """Sanitize name for use as filename."""
    # Replace problematic characters
    name = name.replace("/", "-").replace("\\", "-").replace(":", "-")
    name = name.replace("*", "-").replace("?", "-").replace('"', "-")
    name = name.replace("|", "-").replace("<", "-").replace(">", "-")
    # Remove leading/trailing dots or spaces
    name = name.strip(". ")
    return name


def create_or_update_note(
    entity: Entity,
    output_dir: Path,
    source_file: str,
    update_existing: bool = True,
    config: Optional[config_module.Config] = None
):
    """Create or update a note for an entity."""
    notes_dir = get_notes_dir(output_dir, config)
    
    if entity.entity_type == "person":
        note_dir = notes_dir["people"]
    elif entity.entity_type == "organization":
        note_dir = notes_dir["organizations"]
    else:
        note_dir = notes_dir["topics"]
    
    # Create directory if needed
    note_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize name for filename
    filename = sanitize_filename(entity.name)
    if not filename:
        filename = "unnamed"
    note_path = note_dir / f"{filename}.md"
    
    # Check if note exists
    if note_path.exists() and update_existing:
        with open(note_path) as f:
            existing_content = f.read()
        
        # Check if this source already linked
        if source_file in existing_content:
            # Just update description if needed
            if entity.description and entity.description not in existing_content:
                new_content = existing_content.rstrip() + f"\n\n{entity.description}\n"
                with open(note_path, "w") as f:
                    f.write(new_content)
            return
        
        # Add new source to existing note
        new_content = update_note_with_source(existing_content, entity, source_file)
        
        with open(note_path, "w") as f:
            f.write(new_content)
    else:
        # Create new note
        content = create_new_note(entity, source_file)
        with open(note_path, "w") as f:
            f.write(content)


def create_new_note(entity: Entity, source_file: str) -> str:
    """Create content for a new note."""
    content = f"""---
sources: {json.dumps([source_file])}
---

# {entity.name}

"""
    if entity.description:
        content += f"{entity.description}\n"
    
    content += f"\n## Sources\n\n- {source_file}\n"
    
    return content


def update_note_with_source(existing_content: str, entity: Entity, source_file: str) -> str:
    """Add a new source to an existing note."""
    lines = existing_content.split("\n")
    
    # Find where to insert source (after sources list in frontmatter or at end)
    in_frontmatter = False
    frontmatter_end = -1
    sources_line = -1
    
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
            else:
                frontmatter_end = i
                break
        if in_frontmatter and line.strip().startswith("sources:"):
            sources_line = i
    
    # Update frontmatter sources
    if sources_line >= 0:
        # Parse existing sources
        sources_match = re.search(r'sources:\s*\[(.*?)\]', lines[sources_line])
        if sources_match:
            existing_sources = sources_match.group(1).strip('"').split('","')
            if source_file not in "".join(existing_sources):
                # Add new source to list
                existing_sources.append(f'"{source_file}"')
                lines[sources_line] = f"sources: [{', '.join(existing_sources)}]"
    
    # Add to Sources section if exists, otherwise create it
    sources_section_found = False
    for i, line in enumerate(lines):
        if line.strip().lower() == "## sources":
            sources_section_found = True
            # Add source after this line
            lines.insert(i + 1, f"- {source_file}")
            break
    
    if not sources_section_found:
        lines.append(f"\n## Sources\n\n- {source_file}")
    
    return "\n".join(lines)


def process_file(
    file_path: Path,
    output_dir: Path,
    llm: str = "openai",
    model: str | None = None,
    verbose: bool = False,
    config: Optional[config_module.Config] = None
):
    """Process a single markdown file and extract entities."""
    if verbose:
        print(f"Reading: {file_path}")
    
    with open(file_path) as f:
        content = f.read()
    
    if verbose:
        print(f"Extracting entities via {llm}...")
    
    entities = extract_entities_from_content(content, llm=llm, model=model)
    
    # Filter to enabled entity types
    if config:
        entities = [e for e in entities if config_module.is_entity_enabled(e.entity_type, config)]
    
    if verbose:
        print(f"Found {len(entities)} entities")
    
    for entity in entities:
        entity.sources.append(str(file_path))
        create_or_update_note(entity, output_dir, str(file_path), config=config)
        if verbose:
            print(f"  - {entity.entity_type}: {entity.name}")
    
    return entities


def process_batch(
    file_paths: list[Path],
    output_dir: Path,
    llm: str = "openai",
    model: str | None = None,
    verbose: bool = False,
    config: Optional[config_module.Config] = None
) -> list[Entity]:
    """Process multiple files in a single LLM call."""
    if not file_paths:
        return []
    
    # Read all file contents
    files: list[tuple[str, str]] = []
    for fp in file_paths:
        with open(fp) as f:
            files.append((str(fp), f.read()))
    
    if verbose:
        print(f"Extracting entities from {len(files)} files in batch...")
    
    # Extract entities in one call
    entities = extract_entities_from_batch(files, llm=llm, model=model)
    
    # Filter to enabled entity types
    if config:
        entities = [e for e in entities if config_module.is_entity_enabled(e.entity_type, config)]
    
    # Merge entities that appear across files
    merged = merge_entities([entities])
    
    if verbose:
        print(f"Found {len(merged)} unique entities")
    
    # Create/update notes
    for entity in merged:
        for source in entity.sources:
            create_or_update_note(entity, output_dir, source, config=config)
        if verbose:
            print(f"  - {entity.entity_type}: {entity.name} (from {len(entity.sources)} files)")
    
    return merged


def process_directory(
    input_dir: Path,
    output_dir: Path,
    llm: str = "openai",
    model: str | None = None,
    batch_size: int = 5,
    verbose: bool = False,
    use_state: bool = True,
    force: bool = False,
    config: Optional[config_module.Config] = None
):
    """Process all markdown files in a directory with batching and state tracking."""
    md_files = list(input_dir.glob("**/*.md"))
    
    if verbose:
        print(f"Found {len(md_files)} markdown files")
    
    if not md_files:
        if verbose:
            print("No markdown files found")
        return
    
    # Load state for change detection
    state = load_state() if use_state else None
    
    # Filter to only unprocessed/changed files
    if use_state and not force:
        files_to_process = get_unprocessed_files(md_files, state)
        if verbose:
            skipped = len(md_files) - len(files_to_process)
            if skipped > 0:
                print(f"Skipping {skipped} unchanged files")
    else:
        files_to_process = md_files
    
    if not files_to_process:
        if verbose:
            print("All files already processed (use --force to reprocess)")
        return
    
    if verbose:
        print(f"Processing {len(files_to_process)} files")
    
    total_entities = []
    
    # Process in batches
    for i in range(0, len(files_to_process), batch_size):
        batch = files_to_process[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(files_to_process) + batch_size - 1) // batch_size
        
        if verbose:
            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)...")
        
        entities = process_batch(batch, output_dir, llm=llm, model=model, verbose=verbose, config=config)
        
        # Mark files as processed
        if use_state:
            for fp in batch:
                mark_file_processed(fp, state)
        
        total_entities.extend(entities)
    
    # Save state
    if use_state and state:
        import datetime
        state.last_run = datetime.datetime.now().isoformat()
        save_state(state)
    
    if verbose:
        print(f"Total: {len(total_entities)} unique entities extracted")
    
    return total_entities
