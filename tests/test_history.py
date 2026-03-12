from pathlib import Path

from gil_evaluator.history import (
    append_history,
    build_trend_metrics,
    compare_with_latest,
    compare_with_report,
)
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


def test_compare_with_report_detects_flaky_increase(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        (
            '{"verdicts": [{"library": "demo", "compatibility_tier": "Compatible", '
            '"flaky_case_count": 0, "confidence_score": 1.0, "timeout_count": 0}]}'
        ),
        encoding="utf-8",
    )

    current = _verdict("demo", CompatibilityTier.COMPATIBLE, 5.0)
    current.flaky_case_count = 2
    regressions = compare_with_report(report_path, [current])
    assert regressions
    assert regressions[0]["type"] == "flaky_increase"


def test_build_trend_metrics_uses_window(tmp_path: Path) -> None:
    history_path = tmp_path / "history.json"
    append_history(
        history_path,
        [_verdict("demo", CompatibilityTier.COMPATIBLE, 2.0)],
        ["py312", "py313t"],
        20.0,
    )
    append_history(
        history_path,
        [_verdict("demo", CompatibilityTier.WARNING, 12.0)],
        ["py312", "py313t"],
        20.0,
    )

    current = _verdict("demo", CompatibilityTier.WARNING, 20.0)
    metrics = build_trend_metrics(history_path, [current], window=2)
    assert metrics["demo"]["window"] == 2
    assert metrics["demo"]["avg_confidence"] == 1.0
