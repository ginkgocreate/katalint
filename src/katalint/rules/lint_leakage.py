from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from katalint.findings import Finding, FindingCategory, FindingSeverity
from katalint.rules.base import Rule

RULE_ID = "KTL002"


class LintLeakageRule(Rule):
    """Flag agent guidance files that duplicate prescriptive lint/format rules.

    KTL002 ("Lint Leakage") fires only when BOTH of two conditions hold
    (logical AND):

      (a) The file contains at least one PRESCRIPTIVE style directive -- a
          concrete rule a formatter/linter already enforces, such as "use 4
          spaces for indentation", "max line length 88 characters", "never
          leave trailing whitespace", "always add semicolons", or "single
          quotes". Bare mentions of tooling or delegation to it (e.g.
          "linting is enforced by project tooling", "see ruff.toml", "run the
          linter") do NOT count and do NOT fire -- that delegation pattern is
          exactly what the rule wants to encourage.

      (b) A recognised formatter/linter config file (see CONFIG_FILENAMES)
          exists in the same directory as the target file.

    When both hold, the file is duplicating rules that the neighbouring config
    already owns, so exactly one warning is emitted per check() call.

    Known limitation: the pyproject.toml check is presence-only -- it does not
    inspect whether a relevant [tool.*] section is actually configured (it is
    not TOML-section aware).
    """

    id: ClassVar[str] = RULE_ID
    name: ClassVar[str] = "Lint Leakage"
    category: ClassVar[FindingCategory] = "config"
    default_severity: ClassVar[FindingSeverity] = "warning"

    STYLE_DIRECTIVES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("indentation width", r"\b\d+[\s-]?spaces?\b"),
        ("indentation width", r"\b(?:use\s+)?tabs?\s+for\s+indent"),
        ("line length", r"\bline[\s-]?(?:length|width)\b[^.\n]{0,15}\d+"),
        ("line length", r"(?:line|row|width|行|桁|列幅)[^.\n]{0,20}\b\d+\s*(?:characters?|chars?|columns?|cols?)\b"),
        ("line length", r"\b\d+\s*(?:characters?|chars?|columns?|cols?)\b[^.\n]{0,20}(?:line|row|width|行|桁|列幅)"),
        ("trailing whitespace", r"\b(?:no|never|remove|strip|trim|avoid)\b[^.\n]{0,30}trailing\s+whitespace\b"),
        ("semicolons", r"\b(?:always|never|no|add|omit|require)\b[^.\n]{0,20}semicolons?\b"),
        ("quote style", r"\b(?:single|double)\s+quotes?\b"),
    )

    CONFIG_FILENAMES: ClassVar[tuple[str, ...]] = (
        ".prettierrc",
        ".prettierrc.json",
        "prettier.config.js",
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.json",
        "eslint.config.js",
        ".flake8",
        "ruff.toml",
        ".ruff.toml",
        "pyproject.toml",
        ".rubocop.yml",
    )

    def check(self, file: Path) -> list[Finding]:
        try:
            raw = file.read_bytes()
        except OSError:
            return []

        text = raw.decode("utf-8", errors="replace")

        # Condition (a): prescriptive style directives present in the text.
        matched_labels: list[str] = []
        for label, pattern in self.STYLE_DIRECTIVES:
            if re.compile(pattern, re.IGNORECASE).search(text):
                if label not in matched_labels:
                    matched_labels.append(label)

        if not matched_labels:
            return []

        # Condition (b): a recognised config file sits in the same directory.
        found_config: str | None = None
        for candidate in self.CONFIG_FILENAMES:
            if (file.parent / candidate).is_file():
                found_config = candidate
                break

        if found_config is None:
            return []

        labels = ", ".join(matched_labels)
        message = (
            f"File restates prescriptive style rules ({labels}) that are already "
            f"enforced by the formatter/linter config; found {found_config} in the "
            f"same directory."
        )
        suggestion = (
            "Remove the duplicated prescriptive lint/format rules and defer to the "
            f"formatter/linter config ({found_config}) as the single source of truth; "
            "link to it instead of restating individual rules."
        )

        return [
            Finding(
                rule_id=RULE_ID,
                category="config",
                severity="warning",
                file=file.as_posix(),
                line=1,
                message=message,
                suggestion=suggestion,
            )
        ]
