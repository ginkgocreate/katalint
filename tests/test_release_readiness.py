from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseReadinessTests(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def pyproject(self) -> dict:
        return tomllib.loads(self.read("pyproject.toml"))

    def test_release_files_exist(self) -> None:
        for relative_path in [
            "LICENSE",
            "CHANGELOG.md",
            ".github/workflows/katalint.yml",
        ]:
            with self.subTest(relative_path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_package_metadata_is_ready_for_v0_1_0(self) -> None:
        project = self.pyproject()["project"]

        self.assertEqual("katalint", project["name"])
        self.assertEqual(">=3.11", project["requires-python"])
        self.assertEqual("MIT", project["license"])
        self.assertEqual(["LICENSE"], project["license-files"])
        self.assertEqual(["version"], project["dynamic"])
        self.assertIn("authors", project)
        self.assertIn("urls", project)
        self.assertIn("Programming Language :: Python :: 3", project["classifiers"])
        self.assertIn(
            "Topic :: Software Development :: Quality Assurance",
            project["classifiers"],
        )

    def test_runtime_version_is_stable_v0_1_1(self) -> None:
        init_py = self.read("src/katalint/__init__.py")

        self.assertIn('__version__ = "0.1.1"', init_py)

    def test_changelog_documents_v0_1_0(self) -> None:
        changelog = self.read("CHANGELOG.md")

        self.assertIn("## 0.1.1 - 2026-07-19", changelog)
        self.assertIn("## 0.1.0 - 2026-07-09", changelog)
        self.assertIn("KTL001", changelog)
        self.assertIn("KTL104", changelog)
        self.assertIn("No model calls", changelog)

    def test_ci_runs_tests_build_and_dogfood_lint(self) -> None:
        workflow = self.read(".github/workflows/katalint.yml")

        for command in [
            'python -m pip install -e ".[dev]"',
            "pytest -q",
            "python -m build",
            "python -m pip install --force-reinstall dist/katalint-*.whl",
            "katalint --version",
            "katalint explain KTL001",
            "katalint check",
        ]:
            with self.subTest(command=command):
                self.assertIn(command, workflow)

    def test_ci_runs_supported_python_matrix(self) -> None:
        workflow = self.read(".github/workflows/katalint.yml")

        self.assertIn("matrix:", workflow)
        self.assertIn("python-version:", workflow)
        for version in ["3.11", "3.12", "3.13"]:
            with self.subTest(version=version):
                self.assertIn(version, workflow)

    def test_packaged_rule_docs_exist_for_active_rules(self) -> None:
        for rule_id in [
            "KTL001",
            "KTL002",
            "KTL003",
            "KTL004",
            "KTL101",
            "KTL102",
            "KTL103",
            "KTL104",
        ]:
            matches = list((ROOT / "src/katalint/rule_docs").glob(f"{rule_id}-*.md"))
            with self.subTest(rule_id=rule_id):
                self.assertEqual(1, len(matches))


if __name__ == "__main__":
    unittest.main()
