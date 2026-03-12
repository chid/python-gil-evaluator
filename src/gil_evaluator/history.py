from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import CompatibilityTier, LibraryVerdict

TIER_RANK = {
    CompatibilityTier.COMPATIBLE.value: 0,
    CompatibilityTier.WARNING.value: 1,
    CompatibilityTier.INCOMPATIBLE.value: 2,
}


@dataclass(slots=True)
class HistorySnapshot:
    created_at: str
    runtimes: list[str]
    perf_threshold_pct: float
    verdicts: list[dict[str, Any]]


def compare_with_latest(
    history_path: Path, current_verdicts: list[LibraryVerdict]
) -> list[dict[str, Any]]:
    latest = _latest_snapshot(history_path)
    if latest is None:
        return []
    return _compare_with_previous(
        previous={item["library"]: item for item in latest.get("verdicts", [])},
        current_verdicts=current_verdicts,
    )


def compare_with_report(
    report_path: Path, current_verdicts: list[LibraryVerdict]
) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    previous = {item["library"]: item for item in payload.get("verdicts", [])}
    return _compare_with_previous(previous=previous, current_verdicts=current_verdicts)


def build_trend_metrics(
    history_path: Path,
    current_verdicts: list[LibraryVerdict],
    window: int,
) -> dict[str, dict[str, Any]]:
    history = _load_history(history_path)
    if window <= 0:
        return {}
    snapshots = history[-window:]

    metrics: dict[str, dict[str, Any]] = {}
    for verdict in current_verdicts:
        entries: list[dict[str, Any]] = []
        for snapshot in snapshots:
            for item in snapshot.get("verdicts", []):
                if item.get("library") == verdict.library:
                    entries.append(item)
        if not entries:
            continue

        confidences = [float(item.get("confidence_score", 0.0)) for item in entries]
        timeout_counts = [int(item.get("timeout_count", 0)) for item in entries]
        perf_values = [
            float(item["perf_regression_pct"])
            for item in entries
            if item.get("perf_regression_pct") is not None
        ]
        tier_values = [str(item.get("compatibility_tier")) for item in entries]
        tier_worsen_events = _count_tier_worsen_events(tier_values)

        metrics[verdict.library] = {
            "window": len(entries),
            "avg_confidence": round(sum(confidences) / len(confidences), 3),
            "avg_timeout_count": round(sum(timeout_counts) / len(timeout_counts), 3),
            "avg_perf_regression_pct": (
                round(sum(perf_values) / len(perf_values), 3) if perf_values else None
            ),
            "tier_worsen_events": tier_worsen_events,
        }

    return metrics


def append_history(
    history_path: Path,
    verdicts: list[LibraryVerdict],
    runtimes: list[str],
    perf_threshold_pct: float,
) -> None:
    existing = _load_history(history_path)
    snapshot = HistorySnapshot(
        created_at=datetime.now(UTC).isoformat(),
        runtimes=runtimes,
        perf_threshold_pct=perf_threshold_pct,
        verdicts=[item.to_dict() for item in verdicts],
    )
    existing.append(asdict(snapshot))

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")


def _compare_with_previous(
    previous: dict[str, dict[str, Any]],
    current_verdicts: list[LibraryVerdict],
) -> list[dict[str, Any]]:
    regressions: list[dict[str, Any]] = []

    for verdict in current_verdicts:
        prev = previous.get(verdict.library)
        if prev is None:
            continue

        prev_tier = str(prev.get("compatibility_tier"))
        curr_tier = verdict.compatibility_tier.value
        if TIER_RANK[curr_tier] > TIER_RANK.get(prev_tier, -1):
            regressions.append(
                {
                    "library": verdict.library,
                    "type": "tier_regression",
                    "previous": prev_tier,
                    "current": curr_tier,
                }
            )

        prev_perf = prev.get("perf_regression_pct")
        if isinstance(prev_perf, (int, float)) and verdict.perf_regression_pct is not None:
            if verdict.perf_regression_pct - float(prev_perf) >= 10:
                regressions.append(
                    {
                        "library": verdict.library,
                        "type": "perf_regression_delta",
                        "previous": float(prev_perf),
                        "current": verdict.perf_regression_pct,
                    }
                )

        prev_flaky = int(prev.get("flaky_case_count", 0))
        if verdict.flaky_case_count > prev_flaky:
            regressions.append(
                {
                    "library": verdict.library,
                    "type": "flaky_increase",
                    "previous": prev_flaky,
                    "current": verdict.flaky_case_count,
                }
            )

        prev_confidence = float(prev.get("confidence_score", 0.0))
        if prev_confidence - verdict.confidence_score >= 0.15:
            regressions.append(
                {
                    "library": verdict.library,
                    "type": "confidence_drop",
                    "previous": prev_confidence,
                    "current": verdict.confidence_score,
                }
            )

    return regressions


def _count_tier_worsen_events(tiers: list[str]) -> int:
    worsens = 0
    for idx in range(1, len(tiers)):
        if TIER_RANK.get(tiers[idx], 0) > TIER_RANK.get(tiers[idx - 1], 0):
            worsens += 1
    return worsens


def _load_history(history_path: Path) -> list[dict[str, Any]]:
    if not history_path.exists():
        return []
    payload = json.loads(history_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return []
    return payload


def _latest_snapshot(history_path: Path) -> dict[str, Any] | None:
    history = _load_history(history_path)
    if not history:
        return None
    return history[-1]
