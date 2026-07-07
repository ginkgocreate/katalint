import json

from katalint.findings import Finding


EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERNAL_ERROR = 3

RULE_SLUGS = {
    "KTL001": "context-bloat",
    "KTL002": "lint-leakage",
    "KTL003": "blind-references",
    "KTL004": "prohibition-overload",
    "KTL101": "missing-acceptance-criteria",
    "KTL102": "missing-verification-command",
    "KTL103": "missing-handoff-fields",
    "KTL104": "scope-too-wide",
}


def render_findings(findings: list[Finding], output_format: str = "text") -> str:
    if output_format == "json":
        return _render_json(findings)
    if output_format == "text":
        return _render_text(findings)
    raise ValueError(f"unsupported output format: {output_format}")


def exit_code_for_findings(findings: list[Finding]) -> int:
    return EXIT_FINDINGS if findings else EXIT_OK


def _render_json(findings: list[Finding]) -> str:
    return json.dumps([finding.to_dict() for finding in findings], ensure_ascii=False, indent=2)


def _render_text(findings: list[Finding]) -> str:
    grouped: dict[str, list[Finding]] = {}
    for finding in findings:
        grouped.setdefault(finding.file, []).append(finding)

    lines: list[str] = []
    for file in sorted(grouped):
        lines.append(file)
        for finding in grouped[file]:
            lines.append(f"  {finding.severity} {finding.rule_id} {finding.category}/{_rule_slug(finding)}")
            lines.append(f"  {finding.message}")
            lines.append(f"  Suggestion: {finding.suggestion}")

    return "\n".join(lines)


def _rule_slug(finding: Finding) -> str:
    return RULE_SLUGS.get(finding.rule_id, _slug(finding.message))


def _slug(value: str) -> str:
    normalized = value.lower()
    return "".join(character if character.isalnum() else "-" for character in normalized).strip("-")
