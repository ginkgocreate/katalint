from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL003"


class BlindReferencesRule(Rule):
    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Blind References"
    category: ClassVar[FindingCategory] = "config"
    default_severity: ClassVar[FindingSeverity] = "warning"

    VAGUE_PHRASES: ClassVar[tuple[str, ...]] = (
        "the existing process",
        "existing style",
        "the style guide",
        "previous implementation",
        "as before",
        "the usual way",
        "follow the existing pattern",
        "the current approach",
        "like we did before",
        "既存の",
        "従来通り",
        "これまで通り",
        "いつもの",
    )

    _URL_RE: ClassVar[re.Pattern[str]] = re.compile(r"https?://\S+")
    _MD_LINK_RE: ClassVar[re.Pattern[str]] = re.compile(r"\[[^\]\n]+\]\([^)\n]+\)")
    _BACKTICK_PATH_RE: ClassVar[re.Pattern[str]] = re.compile(r"`[^`\n]*[/.][^`\n]*`")
    _BARE_PATH_RE: ClassVar[re.Pattern[str]] = re.compile(r"\b[\w.-]+/[\w./-]+\b")
    _FILE_EXT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\b[\w-]+\.(?:md|py|ts|tsx|js|jsx|json|ya?ml|toml|txt|rst|go|rb|java|sh|cfg|ini)\b",
        re.IGNORECASE,
    )
    _SECTION_RE: ClassVar[re.Pattern[str]] = re.compile(r"section|§|##", re.IGNORECASE)
    _EXPLANATION_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(because|for example|e\.g\.|i\.e\.|namely|specifically)\b", re.IGNORECASE
    )

    _ANCHOR_PATTERNS: ClassVar[tuple[re.Pattern[str], ...]] = (
        _URL_RE,
        _MD_LINK_RE,
        _BACKTICK_PATH_RE,
        _BARE_PATH_RE,
        _FILE_EXT_RE,
        _SECTION_RE,
        _EXPLANATION_RE,
    )

    def check(self, file: Path) -> list[Finding]:
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        lines = text.splitlines()
        findings: list[Finding] = []

        for i, line in enumerate(lines):
            line_num = i + 1
            lowered_line = line.lower()
            is_candidate = any(
                phrase.lower() in lowered_line for phrase in self.VAGUE_PHRASES
            )
            if not is_candidate:
                continue

            window_lines = []
            if i - 1 >= 0:
                window_lines.append(lines[i - 1])
            window_lines.append(lines[i])
            if i + 1 < len(lines):
                window_lines.append(lines[i + 1])
            window_text = "\n".join(window_lines)

            has_anchor = any(
                pattern.search(window_text) for pattern in self._ANCHOR_PATTERNS
            )
            if has_anchor:
                continue

            findings.append(
                Finding(
                    rule_id=self.id,
                    category=self.category,
                    severity="warning",
                    file=file.as_posix(),
                    line=line_num,
                    message=(
                        f"Line {line_num} contains a vague reference without a nearby URL, path, "
                        f"section, or explanation."
                    ),
                    suggestion=(
                        "Replace the vague reference with a concrete link, file path, section "
                        "reference, or an inline explanation of what it means."
                    ),
                )
            )

        return findings
