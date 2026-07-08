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
    candidates = _explicit_candidates(paths, base) if paths is not None else _default_candidates(base)
    targets: dict[str, Target] = {}

    for candidate in candidates:
        absolute_path = candidate.resolve()
        try:
            relative_path = absolute_path.relative_to(base)
        except ValueError:
            continue

        if _is_ignored(relative_path):
            continue

        target = Target(path=relative_path, kind=classify_target(absolute_path, relative_path))
        targets[target.path.as_posix()] = target

    return [targets[key] for key in sorted(targets)]


# Directory prefixes that hold workflow documents (task packets / handoffs).
# A file under one of these keeps PR-1's frontmatter-driven classification and
# is never reclassified as config purely because of its basename.
WORKFLOW_PATH_PREFIXES = (
    ".agent/tasks/",
    "docs/agent/tasks/",
    ".agent/handoffs/",
    "docs/agent/handoffs/",
)


def _is_under_workflow_path(relative_path: Path) -> bool:
    posix = relative_path.as_posix()
    return any(posix.startswith(prefix) for prefix in WORKFLOW_PATH_PREFIXES)


def classify_target(absolute_path: Path, relative_path: Path) -> TargetKind:
    # Classification is location-first, which resolves the tension between a
    # config basename and a `type:` frontmatter cleanly:
    #   1. Under a workflow directory -> task/handoff by frontmatter, else
    #      unknown (a config-named file here is never config; PR-1 behaviour).
    #   2. A config file by basename anywhere else -> config (frontmatter does
    #      not turn a genuine config file into a workflow document).
    #   3. Otherwise -> honour an explicit task/handoff frontmatter, else unknown.
    if _is_under_workflow_path(relative_path):
        frontmatter_type = _read_frontmatter_type(absolute_path)
        return frontmatter_type if frontmatter_type in {"task", "handoff"} else "unknown"

    if _is_config_path(relative_path):
        return "config"

    frontmatter_type = _read_frontmatter_type(absolute_path)
    return frontmatter_type if frontmatter_type in {"task", "handoff"} else "unknown"


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
    # Config files are identified by basename at any depth, so an explicitly
    # passed path (e.g. `katalint check pkg/AGENTS.md`) or a nested config file
    # surfaced by a directory scan is classified as config, not unknown. Default
    # discovery only ever surfaces root-level config + .claude/agents via its
    # glob patterns, so this basename rule does not widen the default scan.
    if relative_path.name in CONFIG_FILES:
        return True

    # Subagent definitions: a `.md` that is a DIRECT child of a `.claude/agents`
    # directory (matches the documented `.claude/agents/*.md` glob). The
    # `.claude/agents` pair may sit under a nested-repo prefix, but files in
    # deeper subdirectories are not subagent definitions.
    parent = relative_path.parent
    return (
        relative_path.suffix == ".md"
        and parent.name == "agents"
        and parent.parent.name == ".claude"
    )


def _read_frontmatter_type(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return None

    if not lines or lines[0].strip() != "---":
        return None

    found_type: str | None = None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            return found_type

        if found_type is None:
            match = FRONTMATTER_TYPE_RE.match(stripped)
            if match:
                found_type = match.group(1).lower()

    return None


def _is_ignored(relative_path: Path) -> bool:
    return any(part in IGNORE_DIR_NAMES for part in relative_path.parts)
