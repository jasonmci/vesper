#!/usr/bin/env python3
"""
Main entry point for Vesper application.
"""

import click

from vesper.app import VesperApp


@click.command()
@click.option(
    "--file", "-f", type=click.Path(exists=False), help="File to open on startup"
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["editor", "outliner", "tasks"]),
    default="editor",
    help="Starting mode",
)
@click.version_option()
def main(file: str | None = None, mode: str = "editor") -> None:
    """Vesper - Terminal-based text editor, outliner, and task tracker."""
    app = VesperApp()

    if file:
        app.initial_file = file

    app.initial_mode = mode
    app.run()


if __name__ == "__main__":
    main()
