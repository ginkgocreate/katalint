from pathlib import Path
from typing import Annotated

import typer

from katalint import __version__
from katalint.discovery import Target, discover_targets
from katalint.findings import Finding
from katalint.reporter import (
    EXIT_INTERNAL_ERROR,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    exit_code_for_findings,
    render_findings,
)
from katalint.rules.base import Rule, load_rules


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
    output_format: Annotated[
        str,
        typer.Option("--format", help="Output format: text or json."),
    ] = "text",
    list_targets: Annotated[
        bool,
        typer.Option("--list-targets", help="List discovered targets and exit."),
    ] = False,
) -> None:
    if output_format not in {"text", "json"}:
        typer.echo(f"Unsupported format: {output_format}", err=True)
        raise typer.Exit(EXIT_USAGE_ERROR)

    try:
        targets = discover_targets(paths=paths)
        if list_targets:
            _print_targets(targets)
            raise typer.Exit(EXIT_OK)

        rules = load_rules()
        findings = _run_rules(targets, rules)
        rendered = render_findings(findings, output_format=output_format)
        if rendered:
            typer.echo(rendered)
        raise typer.Exit(exit_code_for_findings(findings))
    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"internal error: {error}", err=True)
        raise typer.Exit(EXIT_INTERNAL_ERROR) from error


@app.command()
def explain(rule_id: str) -> None:
    normalized_rule_id = rule_id.upper()
    docs = sorted(_rules_docs_dir().glob(f"{normalized_rule_id}-*.md"))
    if not docs:
        typer.echo(f"{normalized_rule_id} is 未実装/予約.")
        raise typer.Exit(EXIT_OK)

    typer.echo(docs[0].read_text(encoding="utf-8"))


def _print_targets(targets: list[Target]) -> None:
    for target in targets:
        typer.echo(f"{target.path.as_posix()}\t{target.kind}")


def _run_rules(targets: list[Target], rules: list[Rule]) -> list[Finding]:
    findings: list[Finding] = []
    for target in targets:
        for rule in rules:
            if rule.applies_to(target.kind):
                findings.extend(rule.check(target.path))
    return findings


def _rules_docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "rules"
