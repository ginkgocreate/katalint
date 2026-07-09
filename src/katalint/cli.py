from dataclasses import replace
import fnmatch
import hashlib
from importlib import resources
from importlib.resources.abc import Traversable
import json
from pathlib import Path
import re
from typing import Annotated

import typer

from katalint import __version__
from katalint.config import (
    ConfigError,
    KatalintConfig,
    expand_target_patterns,
    load_config,
)
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

SUPPRESSION_RE = re.compile(r"<!--\s*katalint-disable\s+([^:>]+):\s*(.*?)\s*-->")


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
    config_path: Annotated[
        Path | None,
        typer.Option("--config", help="Path to katalint.yml."),
    ] = None,
    baseline_path: Annotated[
        Path | None,
        typer.Option("--baseline", help="Filter findings present in a baseline file."),
    ] = None,
    write_baseline: Annotated[
        Path | None,
        typer.Option(
            "--write-baseline",
            help="Write current findings to a baseline file and exit.",
        ),
    ] = None,
) -> None:
    if output_format not in {"text", "json"}:
        typer.echo(f"Unsupported format: {output_format}", err=True)
        raise typer.Exit(EXIT_USAGE_ERROR)

    try:
        root = Path.cwd()
        config = load_config(root=root, config_path=config_path)
        target_paths = _target_paths(paths, config, root)
        targets = _filter_ignored_targets(discover_targets(paths=target_paths), config.ignore)
        if list_targets:
            _print_targets(targets)
            raise typer.Exit(EXIT_OK)

        rules = load_rules()
        _configure_rules(rules, config)
        findings = _run_rules(targets, rules, config)
        findings = _filter_suppressed_findings(findings, root)

        if write_baseline is not None:
            _write_baseline(_resolve_cli_path(root, write_baseline), findings)
            raise typer.Exit(EXIT_OK)

        baseline = _resolve_baseline_path(root, baseline_path, config)
        if baseline is not None:
            findings = _filter_baselined_findings(findings, baseline)

        rendered = render_findings(findings, output_format=output_format)
        if rendered:
            typer.echo(rendered)
        raise typer.Exit(exit_code_for_findings(findings, fail_on=config.fail_on))
    except typer.Exit:
        raise
    except ConfigError as error:
        typer.echo(f"config error: {error}", err=True)
        raise typer.Exit(EXIT_USAGE_ERROR) from error
    except Exception as error:
        typer.echo(f"internal error: {error}", err=True)
        raise typer.Exit(EXIT_INTERNAL_ERROR) from error


@app.command()
def explain(rule_id: str) -> None:
    normalized_rule_id = rule_id.upper()
    doc = _find_rule_doc(normalized_rule_id)
    if doc is None:
        typer.echo(f"{normalized_rule_id} is 未実装/予約.")
        raise typer.Exit(EXIT_OK)

    typer.echo(doc.read_text(encoding="utf-8"))


def _print_targets(targets: list[Target]) -> None:
    for target in targets:
        typer.echo(f"{target.path.as_posix()}\t{target.kind}")


def _target_paths(
    paths: list[Path] | None,
    config: KatalintConfig,
    root: Path,
) -> list[Path] | None:
    if paths is not None:
        return paths
    if config.target_patterns is not None:
        return expand_target_patterns(root, config.target_patterns)
    return None


def _filter_ignored_targets(
    targets: list[Target],
    ignore_patterns: tuple[str, ...],
) -> list[Target]:
    if not ignore_patterns:
        return targets
    return [
        target
        for target in targets
        if not _matches_any_ignore(target.path.as_posix(), ignore_patterns)
    ]


def _matches_any_ignore(path: str, ignore_patterns: tuple[str, ...]) -> bool:
    for pattern in ignore_patterns:
        normalized = pattern.strip("/")
        if pattern.endswith("/**") and (
            path == normalized[:-3] or path.startswith(f"{normalized[:-3]}/")
        ):
            return True
        if fnmatch.fnmatchcase(path, pattern):
            return True
    return False


def _configure_rules(rules: list[Rule], config: KatalintConfig) -> None:
    for rule in rules:
        settings = config.rules.get(rule.id)
        if settings is None:
            continue
        for option, value in settings.options.items():
            if not hasattr(rule, option):
                raise ConfigError(f"rules.{rule.id}.{option} is not a supported option")
            setattr(rule, option, value)


def _run_rules(
    targets: list[Target],
    rules: list[Rule],
    config: KatalintConfig,
) -> list[Finding]:
    findings: list[Finding] = []
    for target in targets:
        for rule in rules:
            if rule.applies_to(target.kind):
                for finding in rule.check(target.path):
                    findings.append(_apply_severity_override(finding, config))
    return findings


def _apply_severity_override(finding: Finding, config: KatalintConfig) -> Finding:
    settings = config.rules.get(finding.rule_id)
    if settings is None or settings.severity is None:
        return finding
    return replace(finding, severity=settings.severity)


def _filter_suppressed_findings(findings: list[Finding], root: Path) -> list[Finding]:
    suppressed_by_file: dict[str, set[str]] = {}
    return [
        finding
        for finding in findings
        if not _is_suppressed(finding, root, suppressed_by_file)
    ]


def _is_suppressed(
    finding: Finding,
    root: Path,
    suppressed_by_file: dict[str, set[str]],
) -> bool:
    if finding.file not in suppressed_by_file:
        path = Path(finding.file)
        absolute_path = path if path.is_absolute() else root / path
        suppressed_by_file[finding.file] = _read_suppressed_rules(absolute_path)

    suppressed_rules = suppressed_by_file[finding.file]
    return "ALL" in suppressed_rules or finding.rule_id in suppressed_rules


def _read_suppressed_rules(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()

    rules: set[str] = set()
    for match in SUPPRESSION_RE.finditer(text):
        raw_rules = match.group(1)
        reason = match.group(2).strip()
        if not reason:
            continue
        rules.update(
            rule_id.upper()
            for rule_id in re.split(r"[\s,]+", raw_rules)
            if rule_id
        )
    return rules


def _resolve_baseline_path(
    root: Path,
    baseline_path: Path | None,
    config: KatalintConfig,
) -> Path | None:
    if baseline_path is not None:
        return _resolve_cli_path(root, baseline_path)
    return config.baseline


def _resolve_cli_path(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _write_baseline(path: Path, findings: list[Finding]) -> None:
    payload = {
        "version": 1,
        "findings": [
            {
                "fingerprint": _finding_fingerprint(finding),
                "rule_id": finding.rule_id,
                "file": finding.file,
                "line": finding.line,
                "message": finding.message,
            }
            for finding in findings
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _filter_baselined_findings(findings: list[Finding], baseline_path: Path) -> list[Finding]:
    fingerprints = _read_baseline_fingerprints(baseline_path)
    return [
        finding
        for finding in findings
        if _finding_fingerprint(finding) not in fingerprints
    ]


def _read_baseline_fingerprints(path: Path) -> set[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ConfigError(f"{path}: cannot read baseline: {error}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"{path}: invalid baseline JSON: {error}") from error

    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ConfigError(f"{path}: baseline must be a version 1 object")

    raw_findings = payload.get("findings", [])
    if not isinstance(raw_findings, list):
        raise ConfigError(f"{path}: baseline findings must be a list")

    fingerprints: set[str] = set()
    for raw_finding in raw_findings:
        if isinstance(raw_finding, dict) and isinstance(raw_finding.get("fingerprint"), str):
            fingerprints.add(raw_finding["fingerprint"])
    return fingerprints


def _finding_fingerprint(finding: Finding) -> str:
    payload = "\0".join(
        [
            finding.rule_id,
            finding.file,
            str(finding.line),
            finding.message,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_rule_doc(rule_id: str) -> Traversable | Path | None:
    source_docs = sorted(_repo_rules_docs_dir().glob(f"{rule_id}-*.md"))
    if source_docs:
        return source_docs[0]

    packaged_docs = resources.files("katalint.rule_docs")
    for doc in sorted(packaged_docs.iterdir(), key=lambda item: item.name):
        if doc.name.startswith(f"{rule_id}-") and doc.name.endswith(".md"):
            return doc
    return None


def _repo_rules_docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "rules"
