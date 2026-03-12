from gil_evaluator.models import CompatibilityTier, ScenarioResult, ScenarioStatus
from gil_evaluator.scoring import score_results


def test_scoring_marks_incompatible_on_critical_failure() -> None:
    results = [
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py312",
            status=ScenarioStatus.SUCCESS,
            duration_ms=10,
            metadata={"case_type": "perf"},
        ),
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py313t",
            status=ScenarioStatus.ERROR,
            duration_ms=10,
            metadata={"case_type": "perf"},
            error_type="RuntimeError",
            error_message="boom",
        ),
    ]

    verdict = score_results(results)[0]
    assert verdict.compatibility_tier == CompatibilityTier.INCOMPATIBLE
    assert verdict.failure_count == 1
    assert verdict.crash_count == 1


def test_scoring_marks_warning_on_perf_threshold() -> None:
    results = [
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py312",
            status=ScenarioStatus.SUCCESS,
            duration_ms=100,
            metadata={"case_type": "perf"},
        ),
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py313t",
            status=ScenarioStatus.SUCCESS,
            duration_ms=120,
            metadata={"case_type": "perf"},
        ),
    ]

    verdict = score_results(results, perf_threshold_pct=20.0)[0]
    assert verdict.compatibility_tier == CompatibilityTier.WARNING
    assert verdict.perf_regression_pct == 20.0


def test_scoring_marks_compatible_when_no_critical_or_perf_issue() -> None:
    results = [
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py312",
            status=ScenarioStatus.SUCCESS,
            duration_ms=100,
            metadata={"case_type": "perf"},
        ),
        ScenarioResult(
            library="demo",
            scenario_id="demo.perf",
            runtime="py313t",
            status=ScenarioStatus.SUCCESS,
            duration_ms=109,
            metadata={"case_type": "perf"},
        ),
    ]

    verdict = score_results(results, perf_threshold_pct=20.0)[0]
    assert verdict.compatibility_tier == CompatibilityTier.COMPATIBLE
