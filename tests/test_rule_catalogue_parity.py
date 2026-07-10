from pathlib import Path
import re

from katalint.reporter import RULE_SLUGS
from katalint.rules.base import load_rules


ROOT = Path(__file__).resolve().parents[1]


def test_rule_ids_match_docs_package_docs_and_reporter_slugs() -> None:
    code_rule_ids = [rule.id for rule in load_rules()]
    docs_rule_ids = _documented_active_rule_ids()
    repo_doc_ids = _rule_doc_ids(ROOT / "docs/rules")
    package_doc_ids = _rule_doc_ids(ROOT / "src/katalint/rule_docs")
    reporter_rule_ids = list(RULE_SLUGS)

    _assert_unique(code_rule_ids)
    _assert_unique(docs_rule_ids)
    _assert_unique(repo_doc_ids)
    _assert_unique(package_doc_ids)
    _assert_unique(reporter_rule_ids)

    expected = set(code_rule_ids)
    assert expected == set(docs_rule_ids)
    assert expected == set(repo_doc_ids)
    assert expected == set(package_doc_ids)
    assert expected == set(reporter_rule_ids)


def _documented_active_rule_ids() -> list[str]:
    index = (ROOT / "docs/rules/index.md").read_text(encoding="utf-8")
    match = re.search(
        r"## v0 active rules\n(?P<body>.*?)\n## Reserved rules",
        index,
        flags=re.DOTALL,
    )
    assert match is not None
    return re.findall(r"\| (KTL\d{3}) \|", match.group("body"))


def _rule_doc_ids(directory: Path) -> list[str]:
    return [
        path.name.split("-", maxsplit=1)[0]
        for path in directory.glob("KTL*.md")
    ]


def _assert_unique(rule_ids: list[str]) -> None:
    assert len(rule_ids) == len(set(rule_ids))
