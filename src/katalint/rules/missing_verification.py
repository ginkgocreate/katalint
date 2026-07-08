from __future__ import annotations

from pathlib import Path
import re
from typing import ClassVar

from katalint.discovery import TargetKind
from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL102"

_SUGGESTION = (
    'Add a "Commands to run" or "Verification" section with at least one '
    "runnable test/lint/build command, such as `pytest -q`, so the task packet "
    "can be verified before it is considered done."
)

# Commands unambiguous enough to credit wherever they appear -- these strings do
# not occur incidentally in prose, so a plain substring match is safe.
_STRONG_COMMANDS: tuple[str, ...] = (
    "pytest",
    "npm test",
    "npm run",
    "yarn test",
    "make test",
    "go test",
    "cargo test",
    "mvn test",
    "./gradlew",
)

# Generic single words that also occur in ordinary prose ("Build the signup
# page", "lint the copy"). These are credited ONLY when they appear inside a
# command/code context so a bare prose mention does not satisfy the rule.
_GENERIC_COMMANDS: tuple[str, ...] = (
    "build",
    "lint",
    "tsc",
    "typecheck",
)

# Toggles a fenced code block: ``` or ~~~ optionally followed by an info string.
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
# Inline code spans: `...`.
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")


class MissingVerificationRule(Rule):
    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Missing Verification Command"
    category: ClassVar[FindingCategory] = "workflow"
    default_severity: ClassVar[FindingSeverity] = "error"
    target_kinds: ClassVar[tuple[TargetKind, ...]] = ("task",)

    VERIFY_HEADINGS: ClassVar[tuple[str, ...]] = (
        "Verification",
        "Commands to run",
        "How to test",
        "Testing",
        "検証",
        "コマンド",
    )

    # Unambiguous commands credited anywhere in the text.
    STRONG_COMMANDS: ClassVar[tuple[str, ...]] = _STRONG_COMMANDS
    # Generic words credited only inside a command/code context.
    GENERIC_COMMANDS: ClassVar[tuple[str, ...]] = _GENERIC_COMMANDS
    # Full vocabulary, retained for documentation/reference.
    COMMAND_VOCAB: ClassVar[tuple[str, ...]] = _STRONG_COMMANDS + _GENERIC_COMMANDS

    def check(self, file: Path) -> list[Finding]:
        try:
            raw = file.read_bytes()
        except OSError:
            return []

        text = raw.decode("utf-8", errors="replace")
        verify_headings = {heading.lower() for heading in self.VERIFY_HEADINGS}

        heading_present = False
        command_context_parts: list[str] = []
        in_fence = False

        for line in text.splitlines():
            if _FENCE_RE.match(line):
                in_fence = not in_fence
                continue

            if in_fence:
                # Fenced code is command context; headings inside it are ignored.
                command_context_parts.append(line)
                continue

            # Inline code spans are command context.
            for match in _INLINE_CODE_RE.finditer(line):
                command_context_parts.append(match.group(1))

            stripped = line.strip()

            # Shell/prompt lines are command context.
            if stripped.startswith("$"):
                command_context_parts.append(stripped[1:])

            # ATX heading detection (only outside fenced code blocks). Strip
            # both the leading `#` markers and any optional closing `#` sequence.
            if stripped.startswith("#"):
                heading = stripped.lstrip("#").strip().rstrip("#").strip()
                if heading.lower() in verify_headings:
                    heading_present = True

        lower_text = text.lower()
        command_context = "\n".join(command_context_parts).lower()

        strong_present = any(cmd in lower_text for cmd in self.STRONG_COMMANDS)
        generic_present = any(cmd in command_context for cmd in self.GENERIC_COMMANDS)
        command_present = strong_present or generic_present

        if heading_present or command_present:
            return []

        return [
            Finding(
                rule_id=self.id,
                category=self.category,
                severity="error",
                file=file.as_posix(),
                line=1,
                message=f"{file.name} has no verification command or section.",
                suggestion=_SUGGESTION,
            )
        ]
