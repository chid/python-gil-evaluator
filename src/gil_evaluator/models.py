from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ScenarioStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class CompatibilityTier(StrEnum):
    COMPATIBLE = "Compatible"
    WARNING = "Warning"
    INCOMPATIBLE = "Incompatible"


@dataclass(slots=True)
class ScenarioResult:
    library: str
    scenario_id: str
    runtime: str
    status: ScenarioStatus
    duration_ms: float
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LibraryVerdict:
    library: str
    compatibility_tier: CompatibilityTier
    failure_count: int
    crash_count: int
    perf_regression_pct: float | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["compatibility_tier"] = self.compatibility_tier.value
        return payload


@dataclass(slots=True)
class Report:
    results: list[ScenarioResult]
    verdicts: list[LibraryVerdict]
    runtimes: list[str]
    perf_threshold_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtimes": self.runtimes,
            "perf_threshold_pct": self.perf_threshold_pct,
            "results": [result.to_dict() for result in self.results],
            "verdicts": [verdict.to_dict() for verdict in self.verdicts],
        }
