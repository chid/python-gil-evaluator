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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LibraryVerdict":
        return cls(
            library=payload["library"],
            compatibility_tier=CompatibilityTier(payload["compatibility_tier"]),
            failure_count=int(payload.get("failure_count", 0)),
            crash_count=int(payload.get("crash_count", 0)),
            flaky_case_count=int(payload.get("flaky_case_count", 0)),
            timeout_count=int(payload.get("timeout_count", 0)),
            confidence_score=float(payload.get("confidence_score", 0.0)),
            perf_regression_pct=(
                float(payload["perf_regression_pct"])
                if payload.get("perf_regression_pct") is not None
                else None
            ),
            notes=list(payload.get("notes", [])),
        )


@dataclass(slots=True)
class Report:
    results: list[ScenarioResult]
    verdicts: list[LibraryVerdict]
    runtimes: list[str]
    perf_threshold_pct: float
    history_regressions: list[dict[str, Any]] = field(default_factory=list)
    regression_deltas: list[dict[str, Any]] = field(default_factory=list)
    trend_metrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    adapter_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    profile: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "runtimes": self.runtimes,
            "profile": self.profile,
            "perf_threshold_pct": self.perf_threshold_pct,
            "results": [result.to_dict() for result in self.results],
            "verdicts": [verdict.to_dict() for verdict in self.verdicts],
            "history_regressions": self.history_regressions,
            "regression_deltas": self.regression_deltas,
            "trend_metrics": self.trend_metrics,
            "adapter_metadata": self.adapter_metadata,
        }
