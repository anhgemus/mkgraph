"""Prompt templates for entity extraction."""


def get_extraction_prompt(content: str) -> str:
    """Generate prompt for extracting entities from a single markdown content."""
    return f"""You are an expert at extracting structured information from documents.

Given the following markdown content, extract all relevant entities and return a JSON array.

## Entity Types

1. **person** - Individual people mentioned (by name)
2. **organization** - Companies, teams, groups, institutions
3. **topic** - Projects, products, concepts, events

## Rules

- Only extract entities that are explicitly mentioned by name
- For each entity, provide a brief description (1-2 sentences)
- Use the exact name as it appears in the text
- Return ONLY valid JSON array, no markdown formatting
- If no entities found, return empty array []

## Output Format

```json
[
  {{"name": "Entity Name", "type": "person|organization|topic", "description": "Brief description"}},
  ...
]
```

## Content to Process

---
{content}
---

Return the JSON array now:"""


def get_batch_extraction_prompt(files: list[tuple[str, str]]) -> str:
    """Generate prompt for extracting entities from multiple files at once."""
    prompt = """You are an expert at extracting structured information from documents.

Given multiple markdown files, extract all relevant entities and return a JSON array.

## Entity Types

1. **person** - Individual people mentioned (by name)
2. **organization** - Companies, teams, groups, institutions
3. **topic** - Projects, products, concepts, events

## Rules

- Only extract entities that are explicitly mentioned by name
- For each entity, provide a brief description (1-2 sentences)
- Use the exact name as it appears in the text
- Track which file each entity came from using the "source" field
- Return ONLY valid JSON array, no markdown formatting
- If no entities found, return empty array []

## Output Format

```json
[
  {"name": "Entity Name", "type": "person|organization|topic", "description": "Brief description", "source": "filename.md"},
  ...
]
```

"""

    # Add each file's content
    for i, (path, content) in enumerate(files, 1):
        filename = path.split("/")[-1]
        prompt += f"\n## File {i}: {filename}\n\n{content}\n"

    prompt += "\n\nReturn the JSON array now:"
    return prompt
