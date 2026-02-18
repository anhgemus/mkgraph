"""Simple CLI for building knowledge graphs from markdown files."""
import os
import json
from pathlib import Path

import click

from mkgraph.processor import process_file, process_directory
from mkgraph.state import load_state, reset_state


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
    "--batch-size",
    "-b",
    type=int,
    default=5,
    help="Number of files to process in each LLM call (for directories)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--no-state",
    is_flag=True,
    help="Disable state tracking (process all files every time)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reprocess all files, ignoring state",
)
def run(
    input_path: str,
    output: str,
    llm: str,
    model: str | None,
    batch_size: int,
    verbose: bool,
    no_state: bool,
    force: bool
):
    """Process a file or directory and create knowledge graph notes."""
    input_p = Path(input_path)
    output_p = Path(output)
    
    if verbose:
        click.echo(f"Input: {input_p}")
        click.echo(f"Output: {output_p}")
        click.echo(f"LLM: {llm}")
        if model:
            click.echo(f"Model: {model}")
        click.echo(f"Batch size: {batch_size}")
        click.echo(f"State tracking: {'disabled' if no_state else 'enabled'}")
        if force:
            click.echo(f"Force reprocess: enabled")
    
    if input_p.is_file():
        click.echo(f"Processing file: {input_p}")
        process_file(input_p, output_p, llm=llm, model=model, verbose=verbose)
        click.echo(f"✓ Done! Notes created in {output_p}")
    else:
        click.echo(f"Processing directory: {input_p}")
        process_directory(
            input_p,
            output_p,
            llm=llm,
            model=model,
            batch_size=batch_size,
            verbose=verbose,
            use_state=not no_state,
            force=force
        )
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
    state = load_state()
    
    click.echo(f"Processed files: {len(state.processed_files)}")
    click.echo(f"Last run: {state.last_run or 'Never'}")


@cli.command()
def reset():
    """Reset state (clear all processed file tracking)."""
    reset_state()
    click.echo("State reset. All files will be reprocessed on next run.")


def main():
    cli()


if __name__ == "__main__":
    main()
