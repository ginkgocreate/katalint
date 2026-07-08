from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL104"


class ScopeTooWideRule(Rule):
    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Scope Too Wide"
    category: ClassVar[FindingCategory] = "workflow"
    default_severity: ClassVar[FindingSeverity] = "warning"
    target_kinds: ClassVar[tuple[str, ...]] = ("task",)

    # -- class-level constants, so PR-5 config can override them later --

    BROAD_GLOB_PATTERNS: ClassVar[tuple[str, ...]] = (
        # Recursive wildcard, but only in a PATH-glob context (adjacent to a
        # "/"): matches src/**, app/**, **/, **/*, /** ... A bare "**text**"
        # Markdown bold span has no adjacent slash and must NOT match.
        r"/\*\*|\*\*/",
        r"(?<![\w/.\-])\*\.[A-Za-z0-9]+\b",
    )

    REPO_WIDE_PHRASES: ClassVar[tuple[str, ...]] = (
        "entire codebase",
        "the whole repo",
        "whole repository",
        "all files",
        "everything",
        "repo-wide",
        "repository-wide",
        "全体",
        "すべてのファイル",
        "全ファイル",
    )

    max_files_per_task: ClassVar[int] = 5

    KNOWN_CODE_EXTENSIONS: ClassVar[tuple[str, ...]] = (
        "py", "ts", "tsx", "js", "jsx", "mjs", "cjs", "go", "rs", "java",
        "rb", "css", "scss", "html", "json", "yaml", "yml", "toml", "md",
        "sh", "c", "cc", "cpp", "h", "hpp", "sql", "kt", "swift",
    )

    def check(self, file: Path) -> list[Finding]:
        try:
            text = file.read_text(encoding="utf-8")
        except OSError:
            return []

        reasons: list[str] = []

        broad_glob = self._find_broad_glob(text)
        if broad_glob is not None:
            reasons.append(f"broad glob '{broad_glob}'")

        phrase = self._find_repo_wide_phrase(text)
        if phrase is not None:
            reasons.append(f"repo-wide wording '{phrase}'")

        file_count = self._count_distinct_files(text)
        if file_count > self.max_files_per_task:
            reasons.append(
                f"task names {file_count} files (limit {self.max_files_per_task})"
            )

        if not reasons:
            return []

        message = (
            f"{file.name} scope is too wide: " + "; ".join(reasons) + "."
        )
        return [
            Finding(
                rule_id=self.id,
                category=self.category,
                severity="warning",
                file=file.as_posix(),
                line=1,
                message=message,
                suggestion=(
                    "Split this task into smaller task packets, or name a "
                    "bounded set of files (5 or fewer) instead of a broad "
                    "glob or repo-wide wording."
                ),
            )
        ]

    # ---- helpers ----

    def _find_broad_glob(self, text: str) -> str | None:
        for pattern in self.BROAD_GLOB_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _find_repo_wide_phrase(self, text: str) -> str | None:
        lowered = text.lower()
        for phrase in self.REPO_WIDE_PHRASES:
            # Japanese phrases: match as-is (no case folding needed).
            needle = phrase if any(ord(ch) > 0x2FFF for ch in phrase) else phrase.lower()
            haystack = text if any(ord(ch) > 0x2FFF for ch in phrase) else lowered
            if needle in haystack:
                return phrase
        return None

    def _count_distinct_files(self, text: str) -> int:
        # Strip fenced code blocks first: we only count files that are
        # explicitly enumerated in prose/lists, not incidental tokens
        # inside example command output or code snippets.
        without_code_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        # Strip URLs so we never mistake a URL path segment for a file path.
        without_urls = re.sub(r"https?://\S+", "", without_code_fences)

        path_token_re = re.compile(
            r"`?([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+"
            r"|[A-Za-z0-9_\-]+\.(?:" + "|".join(self.KNOWN_CODE_EXTENSIONS)
            # Trailing boundary so a full extension is matched: ".tsx" must not
            # be truncated to ".ts", or app.ts and app.tsx would collapse into
            # one token and undercount the file list.
            + r")(?![A-Za-z0-9]))`?"
        )

        distinct: set[str] = set()
        for match in path_token_re.finditer(without_urls):
            token = match.group(1).strip("`").strip(".,;:()[]")
            if not token:
                continue
            distinct.add(token)

        return len(distinct)
