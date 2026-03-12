from pathlib import Path

from gil_evaluator.history import append_history, compare_with_latest
from gil_evaluator.models import CompatibilityTier, LibraryVerdict


def _verdict(
    library: str,
    tier: CompatibilityTier,
    perf: float | None,
) -> LibraryVerdict:
    return LibraryVerdict(
        library=library,
        compatibility_tier=tier,
        failure_count=0,
        crash_count=0,
        flaky_case_count=0,
        timeout_count=0,
        confidence_score=1.0,
        perf_regression_pct=perf,
        notes=[],
    )


def test_history_regression_detects_tier_worsening(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    append_history(
        history_path,
        [_verdict("demo", CompatibilityTier.COMPATIBLE, 5.0)],
        ["py312", "py313t"],
        20.0,
    )

    regressions = compare_with_latest(
        history_path,
        [_verdict("demo", CompatibilityTier.WARNING, 5.0)],
    )

    assert regressions
    assert regressions[0]["type"] == "tier_regression"


def test_history_regression_detects_perf_delta(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    append_history(
        history_path,
        [_verdict("demo", CompatibilityTier.COMPATIBLE, 5.0)],
        ["py312", "py313t"],
        20.0,
    )

    regressions = compare_with_latest(
        history_path,
        [_verdict("demo", CompatibilityTier.COMPATIBLE, 20.5)],
    )

    assert regressions
    assert regressions[0]["type"] == "perf_regression_delta"
