from __future__ import annotations

from collections import defaultdict

from .models import (
    CompatibilityTier,
    LibraryVerdict,
    ScenarioResult,
    ScenarioStatus,
)

CRITICAL_STATUSES = {ScenarioStatus.FAILURE, ScenarioStatus.ERROR, ScenarioStatus.TIMEOUT}


def score_results(
    results: list[ScenarioResult], perf_threshold_pct: float = 20.0
) -> list[LibraryVerdict]:
    by_library: dict[str, list[ScenarioResult]] = defaultdict(list)
    for result in results:
        by_library[result.library].append(result)

    verdicts: list[LibraryVerdict] = []
    for library, library_results in sorted(by_library.items()):
        py313t = [item for item in library_results if item.runtime == "py313t"]
        failures = [item for item in py313t if item.status in CRITICAL_STATUSES]
        crashes = [
            item
            for item in failures
            if item.status in {ScenarioStatus.ERROR, ScenarioStatus.TIMEOUT}
        ]
        timeout_count = sum(1 for item in py313t if item.status in {ScenarioStatus.TIMEOUT})
        flaky_case_count = sum(1 for item in py313t if item.metadata.get("flaky"))
        confidence_score = _confidence_score(py313t)

        regression_pct = _max_perf_regression_pct(library_results)
        notes: list[str] = []

        if failures:
            tier = CompatibilityTier.INCOMPATIBLE
            notes.append("Critical failures detected in free-threaded runtime.")
        elif regression_pct is not None and regression_pct >= perf_threshold_pct:
            tier = CompatibilityTier.WARNING
            notes.append(
                "Performance regression "
                f"{regression_pct:.2f}% exceeds threshold {perf_threshold_pct:.2f}%."
            )
        else:
            tier = CompatibilityTier.COMPATIBLE
            notes.append("No critical failures and no major regression detected.")
        if flaky_case_count > 0:
            notes.append(f"Detected {flaky_case_count} flaky scenario(s) in py313t.")
        if timeout_count > 0:
            notes.append("Timeouts observed; deadlock risk should be investigated.")

        verdicts.append(
            LibraryVerdict(
                library=library,
                compatibility_tier=tier,
                failure_count=len(failures),
                crash_count=len(crashes),
                flaky_case_count=flaky_case_count,
                timeout_count=timeout_count,
                confidence_score=confidence_score,
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


def _confidence_score(results: list[ScenarioResult]) -> float:
    """Higher is better. Penalize failures and flaky behavior."""
    if not results:
        return 0.0
    total = len(results)
    critical = sum(1 for item in results if item.status in CRITICAL_STATUSES)
    flaky = sum(1 for item in results if item.metadata.get("flaky"))
    raw = 1.0 - ((critical * 1.0 + flaky * 0.5) / total)
    return max(0.0, round(raw, 3))
