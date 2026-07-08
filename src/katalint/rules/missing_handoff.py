from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from katalint.discovery import TargetKind
from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL103"


class MissingHandoffFieldsRule(Rule):
    """KTL103 -- flag handoff documents missing one or more required fields."""

    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Missing Handoff Fields"
    category: ClassVar[FindingCategory] = "workflow"
    default_severity: ClassVar[FindingSeverity] = "error"
    target_kinds: ClassVar[tuple[TargetKind, ...]] = ("handoff",)

    # (field_label, accepted_heading_aliases) in the required order.
    required_fields: ClassVar[tuple[tuple[str, frozenset[str]], ...]] = (
        ("Changed Files", frozenset({"Changed Files", "変更ファイル"})),
        ("Commands Run", frozenset({"Commands Run", "実行コマンド"})),
        ("Test Results", frozenset({"Test Results", "テスト結果"})),
        ("Remaining Risks", frozenset({"Remaining Risks", "残リスク", "残存リスク"})),
        ("Next Action", frozenset({"Next Action", "次のアクション", "次アクション"})),
    )

    def check(self, file: Path) -> list[Finding]:
        try:
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []

        present_headings = {
            heading.casefold() for heading in self._collect_headings(text)
        }

        findings: list[Finding] = []
        for label, aliases in self.required_fields:
            is_present = any(
                alias.casefold() in present_headings for alias in aliases
            )
            if is_present:
                continue

            alternates = sorted(alias for alias in aliases if alias != label)
            alt_form = alternates[0] if alternates else label
            findings.append(
                Finding(
                    rule_id=RULE_ID,
                    category="workflow",
                    severity="error",
                    file=file.as_posix(),
                    line=1,
                    message=(
                        f"Handoff document is missing the required "
                        f"'{label}' section."
                    ),
                    suggestion=(
                        f"Add a '## {label}' (or '{alt_form}') section "
                        f"documenting the missing {label} handoff details."
                    ),
                )
            )

        return findings

    @staticmethod
    def _collect_headings(text: str) -> list[str]:
        headings: list[str] = []
        in_fence = False
        fence_marker = ""
        for line in text.splitlines():
            stripped = line.strip()

            # Toggle fenced code blocks (``` or ~~~). Headings shown inside a
            # fence are code examples, not real sections, so skip them.
            if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
                in_fence = True
                fence_marker = stripped[:3]
                continue
            if in_fence:
                if stripped.startswith(fence_marker):
                    in_fence = False
                    fence_marker = ""
                continue

            if not stripped.startswith("#"):
                continue
            idx = 0
            while idx < len(stripped) and stripped[idx] == "#":
                idx += 1
            # Require a space after the run of '#' characters (ATX heading).
            if idx < len(stripped) and stripped[idx] == " ":
                heading = stripped[idx:].strip()
                # Strip optional closing ATX hashes: "## Changed Files ##".
                heading = heading.rstrip("#").strip()
                headings.append(heading)
        return headings
