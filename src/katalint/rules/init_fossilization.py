from __future__ import annotations

from pathlib import Path
import subprocess
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL004"

_CONFIG_FILENAMES = {"AGENTS.md", "CLAUDE.md"}
_SUGGESTION = (
    "Review the agent instruction file and make a small maintenance update, or "
    "remove stale generated content if the file is no longer actively curated."
)


class InitFossilizationRule(Rule):
    """KTL004 -- flag agent config files generated once and never maintained."""

    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Init Fossilization"
    category: ClassVar[FindingCategory] = "config"
    default_severity: ClassVar[FindingSeverity] = "warning"

    max_file_commits: ClassVar[int] = 1
    min_repo_commits: ClassVar[int] = 8

    def check(self, file: Path) -> list[Finding]:
        if file.name not in _CONFIG_FILENAMES:
            return []

        resolved = file.resolve()
        repo_root = _git_root(resolved.parent)
        if repo_root is None:
            return []

        try:
            relative_path = resolved.relative_to(repo_root)
        except ValueError:
            return []

        if not _is_tracked(repo_root, relative_path):
            return []

        repo_commits = _count_repo_commits(repo_root)
        if repo_commits is None or repo_commits < self.min_repo_commits:
            return []

        file_commits = _count_file_commits(repo_root, relative_path)
        if file_commits is None or file_commits > self.max_file_commits:
            return []

        return [
            Finding(
                rule_id=self.id,
                category=self.category,
                severity=self.default_severity,
                file=file.as_posix(),
                line=1,
                message=(
                    f"{file.name} has {file_commits} {_plural(file_commits, 'update')} "
                    f"in Git history while the repository has {repo_commits} "
                    f"repository {_plural(repo_commits, 'commit')}."
                ),
                suggestion=_SUGGESTION,
            )
        ]


def _git_root(path: Path) -> Path | None:
    output = _git(path, "rev-parse", "--show-toplevel")
    if output is None:
        return None
    return Path(output).resolve()


def _is_tracked(repo_root: Path, relative_path: Path) -> bool:
    return _git(repo_root, "ls-files", "--error-unmatch", relative_path.as_posix()) is not None


def _count_repo_commits(repo_root: Path) -> int | None:
    output = _git(repo_root, "rev-list", "--count", "HEAD")
    return _parse_int(output)


def _count_file_commits(repo_root: Path, relative_path: Path) -> int | None:
    output = _git(repo_root, "log", "--format=%H", "--", relative_path.as_posix())
    if output is None:
        return None
    if output == "":
        return 0
    return len(output.splitlines())


def _git(cwd: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _plural(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
