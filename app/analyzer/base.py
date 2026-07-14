from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal


SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
CategoryType = Literal["security", "style", "performance", "maintainability", "business_logic"]


@dataclass
class AnalyzerIssue:
    """A single issue reported by a static analyzer."""

    severity: SeverityLevel
    source: str  # analyzer name: semgrep | bandit | eslint | staticcheck | ...
    message: str
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    rule_id: str | None = None
    category: CategoryType | None = None
    suggestion: str | None = None
    metadata: dict = field(default_factory=dict)

    def dedup_key(self) -> tuple:
        """Key used for deduplication across analyzer results."""
        return (self.file_path, self.line_start, self.rule_id or self.message[:80])


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def normalize_severity(raw: str) -> SeverityLevel:
    """Map raw analyzer severity strings to canonical levels."""
    mapping = {
        "error": "HIGH",
        "warning": "MEDIUM",
        "info": "INFO",
        "note": "INFO",
        "critical": "CRITICAL",
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW",
        # semgrep levels
        "ERROR": "HIGH",
        "WARNING": "MEDIUM",
        "INFO": "INFO",
    }
    return mapping.get(raw, "MEDIUM")  # type: ignore[return-value]


class BaseAnalyzer(ABC):
    """Abstract base class for all static analyzers."""

    name: str = "base"

    @abstractmethod
    async def analyze(self, path: str, **kwargs) -> list[AnalyzerIssue]:
        """Run analysis on the given path and return a list of issues."""
        ...

    def is_enabled(self) -> bool:
        """Override in subclasses to check feature flags."""
        return True
