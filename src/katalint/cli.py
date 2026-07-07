from pathlib import Path
from typing import Annotated

import typer

from katalint import __version__
from katalint.discovery import Target, discover_targets


app = typer.Typer(no_args_is_help=True, invoke_without_command=True)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show katalint version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    return None


@app.command()
def check(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(help="Files or directories to check."),
    ] = None,
    list_targets: Annotated[
        bool,
        typer.Option("--list-targets", help="List discovered targets and exit."),
    ] = False,
) -> None:
    targets = discover_targets(paths=paths)
    if list_targets:
        _print_targets(targets)


def _print_targets(targets: list[Target]) -> None:
    for target in targets:
        typer.echo(f"{target.path.as_posix()}\t{target.kind}")
