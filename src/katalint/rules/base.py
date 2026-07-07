from importlib import import_module
from inspect import getmembers, isclass
from pathlib import Path
import pkgutil
from typing import ClassVar

from katalint.discovery import TargetKind
from katalint.findings import Finding, FindingCategory, FindingSeverity


class Rule:
    id: ClassVar[str]
    category: ClassVar[FindingCategory]
    default_severity: ClassVar[FindingSeverity] = "warning"
    target_kinds: ClassVar[tuple[TargetKind, ...] | None] = None

    def applies_to(self, kind: TargetKind) -> bool:
        if self.target_kinds is not None:
            return kind in self.target_kinds
        if self.category == "config":
            return kind == "config"
        if self.category == "workflow":
            return kind in {"task", "handoff"}
        return False

    def check(self, file: Path) -> list[Finding]:
        raise NotImplementedError


def load_rules(package_name: str = "katalint.rules") -> list[Rule]:
    package = import_module(package_name)
    rules: list[Rule] = []

    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name == "base" or module_info.name.startswith("_"):
            continue

        module = import_module(f"{package_name}.{module_info.name}")
        for _, rule_class in getmembers(module, isclass):
            if _is_concrete_rule(rule_class, module.__name__):
                rules.append(rule_class())

    return sorted(rules, key=lambda rule: rule.id)


def _is_concrete_rule(candidate: type, module_name: str) -> bool:
    return (
        candidate is not Rule
        and issubclass(candidate, Rule)
        and candidate.__module__ == module_name
        and bool(getattr(candidate, "id", None))
    )
