# mkgraph

Turn markdown files into a knowledge graph using LLMs.

## Installation

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

## Options

- `--llm, -l` - LLM provider: openai, anthropic, ollama (default: openai)
- `--model, -m` - Model name (default varies by provider)
- `--output, -o` - Output directory (default: knowledge)
- `--verbose, -v` - Enable verbose logging
