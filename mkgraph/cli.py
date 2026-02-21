"""Simple CLI for building knowledge graphs from markdown files."""
import json
from pathlib import Path

import click

from mkgraph import config as config_module
from mkgraph.processor import process_directory, process_file
from mkgraph.state import load_state


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
    default=None,
    help="LLM provider to use (overrides config)",
)
@click.option(
    "--model",
    type=str,
    default=None,
    help="Model name (overrides config)",
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
    llm: str | None,
    model: str | None,
    batch_size: int,
    verbose: bool,
    no_state: bool,
    force: bool
):
    """Process a file or directory and create knowledge graph notes."""
    # Load config
    cfg = config_module.load_config()

    # CLI args override config
    if llm:
        cfg.llm.provider = llm
    if model:
        cfg.llm.model = model

    input_p = Path(input_path)
    output_p = Path(output)

    if verbose:
        click.echo(f"Input: {input_p}")
        click.echo(f"Output: {output_p}")
        click.echo(f"LLM: {cfg.llm.provider}")
        if cfg.llm.model:
            click.echo(f"Model: {cfg.llm.model}")
        click.echo(f"Batch size: {batch_size}")
        click.echo(f"State tracking: {'disabled' if no_state else 'enabled'}")
        if force:
            click.echo("Force reprocess: enabled")

    if input_p.is_file():
        click.echo(f"Processing file: {input_p}")
        process_file(input_p, output_p, llm=cfg.llm.provider, model=cfg.llm.model, verbose=verbose, config=cfg)
        click.echo(f"✓ Done! Notes created in {output_p}")
    else:
        click.echo(f"Processing directory: {input_p}")
        process_directory(
            input_p,
            output_p,
            llm=cfg.llm.provider,
            model=cfg.llm.model,
            batch_size=batch_size,
            verbose=verbose,
            use_state=not no_state,
            force=force,
            config=cfg
        )
        click.echo(f"✓ Done! Notes created in {output_p}")


@cli.command()
def status():
    """Show processing status and statistics."""
    state = load_state()

    click.echo(f"Processed files: {len(state.processed_files)}")
    click.echo(f"Last run: {state.last_run or 'Never'}")


@cli.command()
def reset():
    """Reset state (clear all processed file tracking)."""
    config_module.reset_state()
    click.echo("State reset. All files will be reprocessed on next run.")


@cli.command()
def init():
    """Initialize config file with defaults."""
    cfg = config_module.load_config()
    config_module.save_config(cfg)
    click.echo(f"Config initialized at {config_module.CONFIG_FILE}")


@cli.command()
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "list_all", is_flag=True, help="List all config settings")
def config(key: str | None, value: str | None, list_all: bool):
    """Get or set configuration values.

    Examples:
        mkgraph config              # Show all config
        mkgraph config llm.provider # Get a value
        mkgraph config llm.provider ollama  # Set a value
    """
    cfg = config_module.load_config()

    if list_all:
        # Show all config as JSON
        click.echo(json.dumps({
            "entity_types": cfg.entity_types,
            "llm": {
                "provider": cfg.llm.provider,
                "model": cfg.llm.model,
                "temperature": cfg.llm.temperature,
            },
            "output_directories": cfg.output_directories,
            "strictness": cfg.strictness,
        }, indent=2))
        return

    if not key:
        click.echo(f"Config file: {config_module.CONFIG_FILE}")
        click.echo("Use 'mkgraph config --list' to see all settings")
        click.echo("Use 'mkgraph config <key> <value>' to set a value")
        return

    # Get or set a value
    parts = key.split(".")

    if not value:
        # Get value
        if len(parts) == 1:
            # Top-level key
            if hasattr(cfg, key):
                click.echo(getattr(cfg, key))
            else:
                click.echo(f"Unknown key: {key}")
        elif len(parts) == 2 and parts[0] == "llm":
            if hasattr(cfg.llm, parts[1]):
                click.echo(getattr(cfg.llm, parts[1]))
            else:
                click.echo(f"Unknown key: {key}")
        else:
            click.echo(f"Unknown key: {key}")
    else:
        # Set value
        if len(parts) == 2 and parts[0] == "llm":
            if parts[1] in ["provider", "model", "temperature", "base_url"]:
                setattr(cfg.llm, parts[1], value if parts[1] != "temperature" else float(value))
                config_module.save_config(cfg)
                click.echo(f"Set {key} = {value}")
            else:
                click.echo(f"Unknown key: {key}")
        elif len(parts) == 1:
            if key in ["strictness"]:
                setattr(cfg, key, value)
                config_module.save_config(cfg)
                click.echo(f"Set {key} = {value}")
            else:
                click.echo(f"Cannot set {key} directly. Use nested keys like 'llm.provider'")
        else:
            click.echo(f"Unknown key: {key}")


def main():
    cli()


if __name__ == "__main__":
    main()
