"""Simple CLI for building knowledge graphs from markdown files."""
import os
import click
from pathlib import Path

from mkgraph.processor import process_file, process_directory


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Turn markdown files into a knowledge graph using LLMs."""
    pass


@cli.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="knowledge",
    help="Output directory for knowledge graph notes",
)
@click.option(
    "--llm",
    type=click.Choice(["openai", "anthropic", "ollama"]),
    default="openai",
    help="LLM provider to use",
)
@click.option(
    "--model",
    type=str,
    help="Model name (default varies by provider)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def run(input_path: str, output: str, llm: str, model: str | None, verbose: bool):
    """Process a file or directory and create knowledge graph notes."""
    input_p = Path(input_path)
    output_p = Path(output)
    
    if verbose:
        click.echo(f"Input: {input_p}")
        click.echo(f"Output: {output_p}")
        click.echo(f"LLM: {llm}")
        if model:
            click.echo(f"Model: {model}")
    
    if input_p.is_file():
        click.echo(f"Processing file: {input_p}")
        process_file(input_p, output_p, llm=llm, model=model, verbose=verbose)
        click.echo(f"✓ Done! Notes created in {output_p}")
    else:
        click.echo(f"Processing directory: {input_p}")
        process_directory(input_p, output_p, llm=llm, model=model, verbose=verbose)
        click.echo(f"✓ Done! Notes created in {output_p}")


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="knowledge",
    help="Output directory for knowledge graph notes",
)
def status(output: str):
    """Show processing status and statistics."""
    output_p = Path(output)
    state_file = Path.home() / ".mkgraph" / "state.json"
    
    if not state_file.exists():
        click.echo("No state file found. Run 'mkgraph run' first.")
        return
    
    import json
    with open(state_file) as f:
        state = json.load(f)
    
    click.echo(f"Processed files: {len(state.get('processed_files', {}))}")
    click.echo(f"Last run: {state.get('last_run', 'Never')}")


def main():
    cli()


if __name__ == "__main__":
    main()
