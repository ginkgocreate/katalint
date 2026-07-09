import json
import os
from pathlib import Path
import unittest

from typer.testing import CliRunner

from katalint.cli import app


ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def invoke_from_root(args: list[str]):
    previous_cwd = Path.cwd()
    os.chdir(ROOT)
    try:
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(previous_cwd)


class ExamplesAndDogfoodingTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_pr6_dogfooding_files_exist(self) -> None:
        for relative_path in [
            "AGENTS.md",
            "CLAUDE.md",
            "katalint.yml",
            ".github/workflows/katalint.yml",
            "docs/examples/pre-commit-config.yaml",
            "docs/examples/bad-task.md",
            "docs/examples/good-task.md",
        ]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_readme_documents_ci_and_examples(self) -> None:
        readme = self.read("README.md")
        for phrase in [
            "GitHub Actions",
            "pre-commit",
            "docs/examples/bad-task.md",
            "docs/examples/good-task.md",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_repository_dogfood_check_exits_successfully(self) -> None:
        result = invoke_from_root(["check"])

        self.assertEqual(0, result.exit_code)

    def test_example_task_packets_show_bad_and_good_outcomes(self) -> None:
        bad_result = invoke_from_root(
            ["check", "docs/examples/bad-task.md", "--format", "json"]
        )
        good_result = invoke_from_root(
            ["check", "docs/examples/good-task.md", "--format", "json"]
        )

        self.assertEqual(1, bad_result.exit_code)
        bad_payload = json.loads(bad_result.output)
        self.assertEqual(
            ["KTL101", "KTL102"],
            [item["rule_id"] for item in bad_payload],
        )

        self.assertEqual(0, good_result.exit_code)
        self.assertEqual([], json.loads(good_result.output))


if __name__ == "__main__":
    unittest.main()
