from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL001"

_SUGGESTION = (
    "Split AGENTS.md into smaller pieces: use nested AGENTS.md files for "
    "subdirectories, extract subagent definitions and task packets into their "
    "own files, and move long-form background into a separate reference doc."
)


class ContextBloatRule(Rule):
    """KTL001 -- flag AGENTS.md files that are too long or too large.

    Two independent detections, each emitting its own ``warning`` Finding:

    * line count strictly greater than ``max_lines`` (``> 200``)
    * byte size greater-than-or-equal to ``max_bytes``
      (``>= 32768``)
    """

    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Context Bloat"
    category: ClassVar[FindingCategory] = "config"
    default_severity: ClassVar[FindingSeverity] = "warning"

    # Class-level constants so config can override them later (PR-5).
    max_lines: ClassVar[int] = 200
    max_bytes: ClassVar[int] = 32768
    configurable_options: ClassVar[dict[str, type]] = {
        "max_lines": int,
        "max_bytes": int,
    }

    def check(self, file: Path) -> list[Finding]:
        try:
            data = file.read_bytes()
        except OSError:
            # Unreadable file: never raise, just report nothing.
            return []

        text = data.decode("utf-8", errors="replace")
        line_count = len(text.splitlines())
        byte_size = len(data)

        findings: list[Finding] = []

        # (a) line count STRICTLY GREATER THAN max_lines  (> 200)
        if line_count > self.max_lines:
            findings.append(
                Finding(
                    rule_id=self.id,
                    category=self.category,
                    severity="warning",
                    file=file.as_posix(),
                    line=1,
                    message=(
                        f"{file.name} has {line_count} lines. "
                        f"Recommended default is {self.max_lines} lines or fewer."
                    ),
                    suggestion=_SUGGESTION,
                )
            )

        # (b) byte size GREATER-THAN-OR-EQUAL max_bytes (>= 32768)
        if byte_size >= self.max_bytes:
            findings.append(
                Finding(
                    rule_id=self.id,
                    category=self.category,
                    severity="warning",
                    file=file.as_posix(),
                    line=1,
                    message=(
                        f"{file.name} is {byte_size} bytes, approaching Codex's "
                        "32 KiB combined instruction-chain budget."
                    ),
                    suggestion=_SUGGESTION,
                )
            )

        return findings
