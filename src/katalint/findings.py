from dataclasses import asdict, dataclass
from typing import Literal


FindingCategory = Literal["config", "workflow"]
FindingSeverity = Literal["warning", "error"]


@dataclass(frozen=True, kw_only=True)
class Finding:
    rule_id: str
    category: FindingCategory
    severity: FindingSeverity = "warning"
    file: str
    line: int
    message: str
    suggestion: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)
