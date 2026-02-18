# mkgraph

Turn markdown files into a knowledge graph using LLMs.

## Installation

### Using uv (recommended)

```bash
# Clone the repo
git clone https://github.com/anhgemus/mkgraph.git
cd mkgraph

# Install with uv (includes dependencies)
uv pip install -e .

# Or with dev dependencies (includes testing tools)
uv pip install -e ".[dev]"
```

### Using pip

```bash
pip install -e .
```

## Setup

Set your LLM API key:

```bash
# For OpenAI
export OPENAI_API_KEY="your-key-here"

# For Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# For Ollama (local)
export OLLAMA_URL="http://localhost:11434"
```

Or configure via CLI:

```bash
mkgraph config llm.provider ollama
mkgraph config llm.model glm-4.7-flash
```

## Usage

Process a single file:
```bash
mkgraph run input.md -o knowledge/
```

Process a directory:
```bash
mkgraph run ./notes/ -o knowledge/
```

Choose LLM provider:
```bash
mkgraph run input.md --llm anthropic --model claude-3-haiku-20240307
```

Verbose output:
```bash
mkgraph run input.md -v
```

Check status:
```bash
mkgraph status
```

## Configuration

View config:
```bash
mkgraph config --list
```

Set values:
```bash
mkgraph config llm.provider ollama
mkgraph config llm.model glm-4.7-flash
mkgraph config strictness high
```

## Options

- `--llm, -l` - LLM provider: openai, anthropic, ollama (default: openai)
- `--model, -m` - Model name (default varies by provider)
- `--output, -o` - Output directory (default: knowledge)
- `--verbose, -v` - Enable verbose logging
- `--batch-size, -b` - Files per batch (default: 5)
- `--force` - Reprocess all files, ignore state
- `--no-state` - Disable state tracking

## Commands

- `mkgraph run` - Process files
- `mkgraph status` - Show processing status
- `mkgraph reset` - Clear state (reprocess all)
- `mkgraph config` - Get/set config
- `mkgraph init` - Initialize config file
