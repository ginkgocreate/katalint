from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


VALID_FAIL_ON = {"warning", "error"}
VALID_SEVERITIES = {"warning", "error"}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class RuleSettings:
    severity: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KatalintConfig:
    fail_on: str = "warning"
    ignore: tuple[str, ...] = ()
    baseline: Path | None = None
    target_patterns: tuple[str, ...] | None = None
    rules: dict[str, RuleSettings] = field(default_factory=dict)


def load_config(
    root: Path | None = None,
    config_path: Path | None = None,
) -> KatalintConfig:
    base = root or Path.cwd()
    path = _resolve_config_path(base, config_path)
    if path is None:
        return KatalintConfig()

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as error:
        raise ConfigError(f"{path}: invalid YAML: {error}") from error
    except OSError as error:
        raise ConfigError(f"{path}: cannot read config: {error}") from error

    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: config must be a mapping")

    version = raw.get("version", 1)
    if version != 1:
        raise ConfigError(f"{path}: unsupported version {version!r}")

    fail_on = raw.get("fail_on", "warning")
    if fail_on not in VALID_FAIL_ON:
        raise ConfigError(f"{path}: fail_on must be one of: error, warning")

    ignore = _as_string_tuple(raw.get("ignore", []), "ignore", path)
    target_patterns = _load_target_patterns(raw.get("targets"), path)
    baseline = _load_baseline_path(raw.get("baseline"), base, path)
    rules = _load_rule_settings(raw.get("rules", {}), path)

    return KatalintConfig(
        fail_on=fail_on,
        ignore=ignore,
        baseline=baseline,
        target_patterns=target_patterns,
        rules=rules,
    )


def expand_target_patterns(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    targets: list[Path] = []
    for pattern in patterns:
        if _is_glob_pattern(pattern):
            targets.extend(path for path in root.glob(pattern) if path.is_file())
        else:
            targets.append(root / pattern)
    return targets


def _resolve_config_path(root: Path, config_path: Path | None) -> Path | None:
    if config_path is not None:
        return config_path if config_path.is_absolute() else root / config_path

    default_path = root / "katalint.yml"
    return default_path if default_path.is_file() else None


def _load_target_patterns(raw_targets: Any, path: Path) -> tuple[str, ...] | None:
    if raw_targets is None:
        return None

    if isinstance(raw_targets, list):
        return _as_string_tuple(raw_targets, "targets", path)

    if not isinstance(raw_targets, dict):
        raise ConfigError(f"{path}: targets must be a mapping or list")

    patterns: list[str] = []
    for key, value in raw_targets.items():
        if not isinstance(key, str):
            raise ConfigError(f"{path}: targets keys must be strings")
        patterns.extend(_as_string_tuple(value, f"targets.{key}", path))
    return tuple(patterns)


def _load_rule_settings(raw_rules: Any, path: Path) -> dict[str, RuleSettings]:
    if raw_rules is None:
        return {}
    if not isinstance(raw_rules, dict):
        raise ConfigError(f"{path}: rules must be a mapping")

    rules: dict[str, RuleSettings] = {}
    for rule_id, raw_settings in raw_rules.items():
        if not isinstance(rule_id, str):
            raise ConfigError(f"{path}: rule IDs must be strings")
        if raw_settings is None:
            rules[rule_id.upper()] = RuleSettings()
            continue
        if not isinstance(raw_settings, dict):
            raise ConfigError(f"{path}: rules.{rule_id} must be a mapping")

        severity = raw_settings.get("severity")
        if severity is not None and severity not in VALID_SEVERITIES:
            raise ConfigError(
                f"{path}: rules.{rule_id}.severity must be warning or error"
            )

        options = {
            key: value
            for key, value in raw_settings.items()
            if key != "severity"
        }
        rules[rule_id.upper()] = RuleSettings(severity=severity, options=options)
    return rules


def _load_baseline_path(raw_baseline: Any, root: Path, path: Path) -> Path | None:
    if raw_baseline is None:
        return None
    if not isinstance(raw_baseline, str):
        raise ConfigError(f"{path}: baseline must be a string path")
    baseline = Path(raw_baseline)
    return baseline if baseline.is_absolute() else root / baseline


def _as_string_tuple(value: Any, field_name: str, path: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigError(f"{path}: {field_name} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ConfigError(f"{path}: {field_name} entries must be strings")
    return tuple(value)


def _is_glob_pattern(pattern: str) -> bool:
    return any(character in pattern for character in "*?[")
