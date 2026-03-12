from gil_evaluator.cases import Case, CaseType
from gil_evaluator.models import ScenarioStatus
from gil_evaluator.runner import RunnerConfig, run_runtime


class MissingAdapter:
    name = "missinglib"

    def import_check(self) -> tuple[bool, str | None]:
        return False, "ModuleNotFoundError: missinglib"

    def functional_cases(self) -> list[Case]:
        return []

    def stress_cases(self) -> list[Case]:
        return []

    def perf_cases(self) -> list[Case]:
        return []


class TinyAdapter:
    name = "tiny"

    def import_check(self) -> tuple[bool, str | None]:
        return True, None

    def functional_cases(self) -> list[Case]:
        return [Case("tiny.functional", CaseType.FUNCTIONAL, lambda: {"ok": 1})]

    def stress_cases(self) -> list[Case]:
        return [Case("tiny.stress", CaseType.STRESS, lambda: {"ok": 1})]

    def perf_cases(self) -> list[Case]:
        return [Case("tiny.perf", CaseType.PERF, lambda: {"ok": 1})]


def test_runner_marks_missing_dependency_as_skipped() -> None:
    results = run_runtime(
        config=RunnerConfig(runtime="py313t"),
        adapters=[MissingAdapter()],
    )

    assert len(results) == 1
    assert results[0].status == ScenarioStatus.SKIPPED
    assert results[0].metadata["reason"] == "dependency_missing"


def test_runner_executes_all_case_types() -> None:
    results = run_runtime(
        config=RunnerConfig(runtime="py312", repeat_perf=2),
        adapters=[TinyAdapter()],
    )

    assert len(results) == 3
    assert {result.metadata["case_type"] for result in results} == {"functional", "stress", "perf"}
    perf = [result for result in results if result.metadata["case_type"] == "perf"][0]
    assert len(perf.metadata["sample_ms"]) == 2
