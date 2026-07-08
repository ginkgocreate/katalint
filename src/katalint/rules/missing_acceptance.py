from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from katalint.discovery import TargetKind
from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL101"

_SUGGESTION = (
    "Add an acceptance-criteria section to this task packet. Use one of the "
    "accepted headings as a real Markdown heading: 'Acceptance Criteria', "
    "'Done When', 'Definition of Done', '完了条件', or '受け入れ条件', followed "
    "by a bulleted list of concrete, testable outcomes."
)


class MissingAcceptanceCriteriaRule(Rule):
    """KTL101 -- flag task packets that have no acceptance-criteria section."""

    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Missing Acceptance Criteria"
    category: ClassVar[FindingCategory] = "workflow"
    default_severity: ClassVar[FindingSeverity] = "error"
    target_kinds: ClassVar[tuple[TargetKind, ...] | None] = ("task",)

    ACCEPTED_HEADINGS: ClassVar[tuple[str, ...]] = (
        "Acceptance Criteria",
        "Done When",
        "Definition of Done",
        "完了条件",
        "受け入れ条件",
    )

    def check(self, file: Path) -> list[Finding]:
        try:
            text = file.read_bytes().decode("utf-8", errors="replace")
        except OSError:
            return []

        accepted = {heading.strip().lower() for heading in self.ACCEPTED_HEADINGS}

        in_fence = False
        fence_marker = ""
        for raw_line in text.splitlines():
            line = raw_line.strip()

            # Toggle fenced-code-block state on ``` or ~~~ fences. Headings that
            # appear inside a fenced code block are examples, not real sections,
            # so they must not suppress the finding.
            if not in_fence and (line.startswith("```") or line.startswith("~~~")):
                in_fence = True
                fence_marker = line[:3]
                continue
            if in_fence:
                if line.startswith(fence_marker):
                    in_fence = False
                continue

            if not line.startswith("#"):
                continue

            hashes_end = 0
            while hashes_end < len(line) and line[hashes_end] == "#":
                hashes_end += 1

            rest = line[hashes_end:]
            # A heading requires the hashes to be followed by whitespace (or end of line).
            if rest and not rest[0].isspace():
                continue

            # Strip the optional closing hash sequence of an ATX heading so that
            # "## Acceptance Criteria ##" matches "Acceptance Criteria".
            heading_text = rest.strip().rstrip("#").strip().lower()
            if heading_text in accepted:
                return []

        return [
            Finding(
                rule_id=RULE_ID,
                category="workflow",
                severity="error",
                file=file.as_posix(),
                line=1,
                message=(
                    f"Task packet '{file.as_posix()}' has no acceptance criteria "
                    "section; add one of the accepted acceptance-criteria headings."
                ),
                suggestion=_SUGGESTION,
            )
        ]
