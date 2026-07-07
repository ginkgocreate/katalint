from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL004"

_SUGGESTION = (
    "Rewrite key prohibitions as positive, testable 'do' instructions, or move "
    "exhaustive prohibition lists to a separate reference document."
)

# ASCII markers are matched with word boundaries so that marker text embedded in
# a larger word (for example "must notify", "do notify", "document", "mustard")
# never false-matches. Japanese markers have no word boundaries and fall back to
# plain substring matching.
_WORD_CHAR = r"[a-z0-9]"


def _count_substring(text_lower: str, marker_lower: str) -> int:
    if not marker_lower:
        return 0
    count = 0
    start = 0
    step = len(marker_lower)
    while True:
        index = text_lower.find(marker_lower, start)
        if index == -1:
            return count
        count += 1
        start = index + step


def _boundary_regex(marker: str, *, exclude_trailing_not: bool = False) -> re.Pattern[str]:
    core = r"\s+".join(re.escape(token) for token in marker.split())
    # For "MUST"/"DO", drop occurrences that are the head of a "MUST NOT"/"DO NOT"
    # prohibition ("not" as a whole word), while still counting "must notify" etc.
    suffix = rf"(?!\s+not(?!{_WORD_CHAR}))" if exclude_trailing_not else ""
    return re.compile(
        rf"(?<!{_WORD_CHAR}){core}(?!{_WORD_CHAR}){suffix}",
        re.IGNORECASE,
    )


def _count_marker(
    text: str,
    text_lower: str,
    marker: str,
    *,
    exclude_trailing_not: bool = False,
) -> int:
    if marker.isascii():
        pattern = _boundary_regex(marker, exclude_trailing_not=exclude_trailing_not)
        return sum(1 for _ in pattern.finditer(text))
    return _count_substring(text_lower, marker.lower())


class ProhibitionOverloadRule(Rule):
    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Prohibition Overload"
    category: ClassVar[FindingCategory] = "config"
    default_severity: ClassVar[FindingSeverity] = "warning"

    PROHIBITION_MARKERS: ClassVar[tuple[str, ...]] = (
        "NEVER",
        "DO NOT",
        "DON'T",
        "MUST NOT",
        "SHALL NOT",
        "禁止",
        "絶対に",
        "してはいけない",
        "するな",
    )

    MUST_DO_MARKERS: ClassVar[tuple[str, ...]] = (
        "MUST",
        "ALWAYS",
        "SHOULD",
        "DO",
        "REQUIRED",
        "してください",
        "すること",
        "必ず",
    )

    # Must-do markers whose bare word also begins a prohibition phrase
    # ("MUST NOT", "DO NOT"); those occurrences must not be credited as must-do.
    _EXCLUDE_TRAILING_NOT: ClassVar[frozenset[str]] = frozenset({"MUST", "DO"})

    max_prohibitions: ClassVar[int] = 5
    min_must_do_ratio: ClassVar[float] = 0.5

    def check(self, file: Path) -> list[Finding]:
        try:
            data = file.read_bytes()
        except OSError:
            return []

        text = data.decode("utf-8", errors="replace")
        text_lower = text.lower()

        prohibition_count = sum(
            _count_marker(text, text_lower, marker)
            for marker in self.PROHIBITION_MARKERS
        )

        must_do_count = sum(
            _count_marker(
                text,
                text_lower,
                marker,
                exclude_trailing_not=marker in self._EXCLUDE_TRAILING_NOT,
            )
            for marker in self.MUST_DO_MARKERS
        )

        denominator = must_do_count + prohibition_count
        if denominator == 0:
            return []

        must_do_ratio = must_do_count / denominator

        if (
            prohibition_count > self.max_prohibitions
            and must_do_ratio < self.min_must_do_ratio
        ):
            return [
                Finding(
                    rule_id=self.id,
                    category=self.category,
                    severity="warning",
                    file=file.as_posix(),
                    line=1,
                    message=(
                        f"{file.name} has {prohibition_count} prohibitions and "
                        f"{must_do_count} must-do instructions (must-do ratio "
                        f"{must_do_ratio:.2f}). Config dominated by prohibitions is "
                        f"hard to act on."
                    ),
                    suggestion=_SUGGESTION,
                )
            ]

        return []
