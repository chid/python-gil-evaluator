from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass

from .adapters import LibraryAdapter, default_adapters
from .cases import Case
from .models import ScenarioResult, ScenarioStatus


@dataclass(slots=True)
class RunnerConfig:
    runtime: str
    timeout_sec: float = 5.0
    repeat_perf: int = 3


def _execute_case(case: Case, timeout_sec: float) -> tuple[ScenarioStatus, float, dict, str | None, str | None]:
    start = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(case.run)
            metadata = fut.result(timeout=timeout_sec) or {}
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ScenarioStatus.SUCCESS, elapsed_ms, metadata, None, None
    except TimeoutError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ScenarioStatus.TIMEOUT, elapsed_ms, {}, type(exc).__name__, "case timed out"
    except Exception as exc:  # pragma: no cover - exercised in integration flows
        elapsed_ms = (time.perf_counter() - start) * 1000
        return ScenarioStatus.ERROR, elapsed_ms, {}, type(exc).__name__, str(exc)


def run_runtime(
    config: RunnerConfig,
    selected_libraries: set[str] | None = None,
    adapters: list[LibraryAdapter] | None = None,
) -> list[ScenarioResult]:
    chosen_adapters = adapters or default_adapters()
    results: list[ScenarioResult] = []

    for adapter in chosen_adapters:
        if selected_libraries and adapter.name not in selected_libraries:
            continue

        import_ok, import_err = adapter.import_check()
        if not import_ok:
            for case_id in ["import_check"]:
                results.append(
                    ScenarioResult(
                        library=adapter.name,
                        scenario_id=f"{adapter.name}.{case_id}",
                        runtime=config.runtime,
                        status=ScenarioStatus.SKIPPED,
                        duration_ms=0.0,
                        error_type="MissingDependency",
                        error_message=import_err,
                        metadata={"reason": "dependency_missing"},
                    )
                )
            continue

        all_cases = adapter.functional_cases() + adapter.stress_cases()
        for case in all_cases:
            status, elapsed_ms, metadata, err_type, err_msg = _execute_case(case, config.timeout_sec)
            results.append(
                ScenarioResult(
                    library=adapter.name,
                    scenario_id=case.case_id,
                    runtime=config.runtime,
                    status=status,
                    duration_ms=elapsed_ms,
                    error_type=err_type,
                    error_message=err_msg,
                    metadata={**metadata, "case_type": case.case_type.value},
                )
            )

        for case in adapter.perf_cases():
            durations: list[float] = []
            meta: dict = {}
            status = ScenarioStatus.SUCCESS
            err_type = None
            err_msg = None
            for _ in range(config.repeat_perf):
                run_status, elapsed_ms, metadata, run_err_type, run_err_msg = _execute_case(
                    case, config.timeout_sec
                )
                if run_status is not ScenarioStatus.SUCCESS:
                    status = run_status
                    err_type = run_err_type
                    err_msg = run_err_msg
                    durations = []
                    break
                durations.append(elapsed_ms)
                meta = metadata

            mean_ms = sum(durations) / len(durations) if durations else 0.0
            results.append(
                ScenarioResult(
                    library=adapter.name,
                    scenario_id=case.case_id,
                    runtime=config.runtime,
                    status=status,
                    duration_ms=mean_ms,
                    error_type=err_type,
                    error_message=err_msg,
                    metadata={
                        **meta,
                        "case_type": case.case_type.value,
                        "repeat_count": config.repeat_perf,
                        "sample_ms": durations,
                    },
                )
            )

    return results
