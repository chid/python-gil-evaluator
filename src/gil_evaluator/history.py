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

    previous = {item["library"]: item for item in latest.get("verdicts", [])}
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

    return regressions


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
