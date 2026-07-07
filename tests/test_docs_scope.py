from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DocumentationScopeTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_pr0_required_documents_exist(self) -> None:
        for relative_path in [
            "README.md",
            "docs/adr/0001-scope.md",
            "docs/rules/index.md",
            "docs/rules/KTL001-context-bloat.md",
            "docs/rules/KTL101-missing-acceptance-criteria.md",
            "SCRATCHPAD.md",
        ]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_readme_linter_positioning_is_explicit(self) -> None:
        readme = self.read("README.md")
        self.assertIn("A fast, deterministic linter for AI coding agent instructions.", readme)
        self.assertIn("It does not run agents, call models, or orchestrate workflows.", readme)
        self.assertIn("one linter", readme)

    def test_readme_documents_out_of_scope_runtime_features(self) -> None:
        readme = self.read("README.md")
        for forbidden_scope in [
            "an agent runtime",
            "a Codex or Claude Code wrapper",
            "a prompt management framework",
            "a model router",
            "an orchestration system",
        ]:
            with self.subTest(forbidden_scope=forbidden_scope):
                self.assertIn(forbidden_scope, readme)

    def test_v0_active_rules_are_documented(self) -> None:
        catalogue = self.read("docs/rules/index.md")
        active_rule_ids = re.findall(r"\| (KTL\d{3}) \|", catalogue)
        self.assertEqual(
            [
                "KTL001",
                "KTL002",
                "KTL003",
                "KTL004",
                "KTL101",
                "KTL102",
                "KTL103",
                "KTL104",
            ],
            active_rule_ids[:8],
        )

    def test_adr_freezes_scope_and_exclusions(self) -> None:
        adr = self.read("docs/adr/0001-scope.md")
        for phrase in [
            "deterministic linter",
            "Running Codex",
            "Running Claude Code",
            "Calling LLMs by default",
            "Network-dependent checks",
            "Autofix in v0",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, adr)


if __name__ == "__main__":
    unittest.main()
