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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScenarioResult":
        return cls(
            library=payload["library"],
            scenario_id=payload["scenario_id"],
            runtime=payload["runtime"],
            status=ScenarioStatus(payload["status"]),
            duration_ms=float(payload["duration_ms"]),
            error_type=payload.get("error_type"),
            error_message=payload.get("error_message"),
            metadata=payload.get("metadata", {}),
        )


@dataclass(slots=True)
class LibraryVerdict:
    library: str
    compatibility_tier: CompatibilityTier
    failure_count: int
    crash_count: int
    flaky_case_count: int
    timeout_count: int
    confidence_score: float
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
    history_regressions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtimes": self.runtimes,
            "perf_threshold_pct": self.perf_threshold_pct,
            "results": [result.to_dict() for result in self.results],
            "verdicts": [verdict.to_dict() for verdict in self.verdicts],
            "history_regressions": self.history_regressions,
        }
