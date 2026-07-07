from dataclasses import dataclass
from pathlib import Path
import re
from typing import Literal, Sequence


TargetKind = Literal["config", "task", "handoff", "unknown"]

CONFIG_FILES = {"AGENTS.md", "AGENTS.override.md", "CLAUDE.md"}
DEFAULT_TARGET_PATTERNS = (
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.md",
    ".claude/agents/*.md",
    ".agent/tasks/**/*.md",
    "docs/agent/tasks/**/*.md",
    ".agent/handoffs/**/*.md",
    "docs/agent/handoffs/**/*.md",
)
IGNORE_DIR_NAMES = {"vendor", "node_modules", ".git", "dist", "build"}
FRONTMATTER_TYPE_RE = re.compile(r"^type\s*:\s*[\"']?([A-Za-z_-]+)[\"']?\s*$")


@dataclass(frozen=True)
class Target:
    path: Path
    kind: TargetKind


def discover_targets(
    paths: Sequence[Path] | None = None,
    root: Path | None = None,
) -> list[Target]:
    base = (root or Path.cwd()).resolve()
    candidates = _explicit_candidates(paths, base) if paths else _default_candidates(base)
    targets: dict[str, Target] = {}

    for candidate in candidates:
        absolute_path = candidate.resolve()
        if _is_ignored(absolute_path, base):
            continue

        relative_path = _relative_to_root(absolute_path, base)
        target = Target(path=relative_path, kind=classify_target(absolute_path, relative_path))
        targets[target.path.as_posix()] = target

    return [targets[key] for key in sorted(targets)]


def classify_target(absolute_path: Path, relative_path: Path) -> TargetKind:
    if _is_config_path(relative_path):
        return "config"

    frontmatter_type = _read_frontmatter_type(absolute_path)
    if frontmatter_type in {"task", "handoff"}:
        return frontmatter_type

    return "unknown"


def _default_candidates(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in DEFAULT_TARGET_PATTERNS:
        candidates.extend(path for path in root.glob(pattern) if path.is_file())
    return candidates


def _explicit_candidates(paths: Sequence[Path], root: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in paths:
        absolute_path = path if path.is_absolute() else root / path
        if absolute_path.is_dir():
            candidates.extend(item for item in absolute_path.rglob("*.md") if item.is_file())
        elif absolute_path.is_file():
            candidates.append(absolute_path)
    return candidates


def _is_config_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if len(parts) == 1 and relative_path.name in CONFIG_FILES:
        return True

    return (
        len(parts) == 3
        and parts[0] == ".claude"
        and parts[1] == "agents"
        and relative_path.suffix == ".md"
    )


def _read_frontmatter_type(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return None

    if not lines or lines[0].strip() != "---":
        return None

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return None

        match = FRONTMATTER_TYPE_RE.match(stripped)
        if match:
            return match.group(1).lower()

    return None


def _is_ignored(path: Path, root: Path) -> bool:
    relative_path = _relative_to_root(path, root)
    return any(part in IGNORE_DIR_NAMES for part in relative_path.parts)


def _relative_to_root(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path
