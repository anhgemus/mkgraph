"""LLM provider abstraction."""
import os
from typing import Literal

import requests

# Try to import clients, handle gracefully if not installed
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


def get_openai_client() -> "OpenAI":
    """Get OpenAI client with API key from env."""
    if not HAS_OPENAI:
        raise ImportError("openai package not installed. Run: pip install openai")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    return OpenAI(api_key=api_key)


def get_anthropic_client() -> "Anthropic":
    """Get Anthropic client with API key from env."""
    if not HAS_ANTHROPIC:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")
    
    return Anthropic(api_key=api_key)


def call_llm(
    prompt: str,
    llm: Literal["openai", "anthropic", "ollama"] = "openai",
    model: str | None = None,
) -> str:
    """Call LLM with prompt and return response text."""
    
    if llm == "openai":
        client = get_openai_client()
        model = model or "gpt-4o-mini"
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    
    elif llm == "anthropic":
        client = get_anthropic_client()
        model = model or "claude-3-haiku-20240307"
        
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    
    elif llm == "ollama":
        # Use Ollama's local API
        model = model or "llama3.2"
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        
        response = requests.post(
            f"{url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json().get("response", "")
    
    else:
        raise ValueError(f"Unknown LLM provider: {llm}")
