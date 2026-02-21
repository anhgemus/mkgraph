"""Prompt templates for entity extraction."""


def get_extraction_prompt(content: str) -> str:
    """Generate prompt for extracting entities from a single markdown content."""
    return f"""You are an expert at extracting structured information from documents.

Given the following content, extract all relevant entities and return a JSON array.

## Entity Types

1. **person** - Individual people mentioned (by name)
2. **organization** - Companies, teams, groups, institutions
3. **topic** - Projects, products, concepts, events, functions, classes

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


def get_docstring_extraction_prompt(content: str, file_type: str = "python") -> str:
    """Generate prompt for extracting entities from code docstrings."""
    lang_hints = {
        "python": "Python code with docstrings (Google, NumPy, or reST style)",
        "javascript": "JavaScript/TypeScript with JSDoc comments",
        "go": "Go code with godoc comments",
        "rust": "Rust code with doc comments",
        "java": "Java code with Javadoc",
    }

    return f"""You are an expert at extracting structured information from {lang_hints.get(file_type, 'code')}.

Given the following code, extract all entities (functions, classes, modules) and return a JSON array.

## Entity Types

1. **person** - Individual authors or maintainers mentioned
2. **organization** - Companies, projects, libraries, frameworks
3. **topic** - Functions, classes, modules, methods, concepts, events

## Rules

- Extract the function/class/module name as the entity name
- For each entity, describe what it does (1-2 sentences)
- Include the entity type in the description (e.g., "Function that...")
- Track dependencies and relationships in the description
- Return ONLY valid JSON array, no markdown formatting
- If no entities found, return empty array []

## Output Format

```json
[
  {{"name": "FunctionName", "type": "topic", "description": "Function that does X, takes Y as input"}},
  {{"name": "ClassName", "type": "topic", "description": "Class for handling Y, inherits from Z"}},
  ...
]
```

## Code to Process

---
{content}
---

Return the JSON array now:"""


def get_batch_extraction_prompt(files: list[tuple[str, str]]) -> str:
    """Generate prompt for extracting entities from multiple files at once."""
    prompt = """You are an expert at extracting structured information from documents.

Given multiple files, extract all relevant entities and return a JSON array.

## Entity Types

1. **person** - Individual people mentioned (by name)
2. **organization** - Companies, teams, groups, institutions
3. **topic** - Projects, products, concepts, events, functions, classes

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
