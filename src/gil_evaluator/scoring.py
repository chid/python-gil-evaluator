from __future__ import annotations

from collections import defaultdict

from .models import CompatibilityTier, LibraryVerdict, ScenarioResult, ScenarioStatus


CRITICAL_STATUSES = {ScenarioStatus.FAILURE, ScenarioStatus.ERROR, ScenarioStatus.TIMEOUT}


def score_results(results: list[ScenarioResult], perf_threshold_pct: float = 20.0) -> list[LibraryVerdict]:
    by_library: dict[str, list[ScenarioResult]] = defaultdict(list)
    for result in results:
        by_library[result.library].append(result)

    verdicts: list[LibraryVerdict] = []
    for library, library_results in sorted(by_library.items()):
        py313t = [item for item in library_results if item.runtime == "py313t"]
        failures = [item for item in py313t if item.status in CRITICAL_STATUSES]
        crashes = [item for item in failures if item.status in {ScenarioStatus.ERROR, ScenarioStatus.TIMEOUT}]

        regression_pct = _max_perf_regression_pct(library_results)
        notes: list[str] = []

        if failures:
            tier = CompatibilityTier.INCOMPATIBLE
            notes.append("Critical failures detected in free-threaded runtime.")
        elif regression_pct is not None and regression_pct >= perf_threshold_pct:
            tier = CompatibilityTier.WARNING
            notes.append(
                f"Performance regression {regression_pct:.2f}% exceeds threshold {perf_threshold_pct:.2f}%."
            )
        else:
            tier = CompatibilityTier.COMPATIBLE
            notes.append("No critical failures and no major regression detected.")

        verdicts.append(
            LibraryVerdict(
                library=library,
                compatibility_tier=tier,
                failure_count=len(failures),
                crash_count=len(crashes),
                perf_regression_pct=regression_pct,
                notes=notes,
            )
        )

    return verdicts


def _max_perf_regression_pct(library_results: list[ScenarioResult]) -> float | None:
    perf312: dict[str, float] = {}
    perf313: dict[str, float] = {}

    for result in library_results:
        if result.metadata.get("case_type") != "perf":
            continue
        if result.status != ScenarioStatus.SUCCESS:
            continue
        if result.runtime == "py312":
            perf312[result.scenario_id] = result.duration_ms
        elif result.runtime == "py313t":
            perf313[result.scenario_id] = result.duration_ms

    regressions: list[float] = []
    for scenario_id, baseline in perf312.items():
        candidate = perf313.get(scenario_id)
        if candidate is None or baseline <= 0:
            continue
        regressions.append(((candidate - baseline) / baseline) * 100)

    if not regressions:
        return None
    return max(regressions)
