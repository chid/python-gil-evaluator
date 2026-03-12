from __future__ import annotations

import json
from subprocess import CompletedProcess

import pytest

from gil_evaluator.models import ScenarioStatus
from gil_evaluator.subprocess_runner import (
    SubprocessConfig,
    parse_runtime_exec_map,
    resolve_runtime_executable,
    run_runtime_in_subprocess,
)


def test_parse_runtime_exec_map() -> None:
    mapping = parse_runtime_exec_map("py312=python3.12,py313t=python3.13t")
    assert mapping == {"py312": "python3.12", "py313t": "python3.13t"}


def test_parse_runtime_exec_map_raises_on_invalid_pair() -> None:
    with pytest.raises(ValueError):
        parse_runtime_exec_map("py312")


def test_resolve_runtime_executable_uses_defaults_and_overrides() -> None:
    assert resolve_runtime_executable("py312", {}) == "python3.12"
    assert resolve_runtime_executable("custom", {}) == "custom"
    assert resolve_runtime_executable("py312", {"py312": "python312-custom"}) == "python312-custom"


def test_run_runtime_in_subprocess_parses_results(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {
            "library": "demo",
            "scenario_id": "demo.case",
            "runtime": "py312",
            "status": "success",
            "duration_ms": 1.2,
            "error_type": None,
            "error_message": None,
            "metadata": {"case_type": "functional"},
        }
    ]

    def fake_run(*_args, **_kwargs):
        return CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr("gil_evaluator.subprocess_runner.subprocess.run", fake_run)

    results = run_runtime_in_subprocess(
        runtime="py312",
        executable="python3.12",
        config=SubprocessConfig(timeout_sec=1.0, repeat_perf=1, repeat_non_perf=2),
        selected_libraries=None,
    )

    assert len(results) == 1
    assert results[0].status is ScenarioStatus.SUCCESS


def test_run_runtime_in_subprocess_handles_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args, **_kwargs):
        return CompletedProcess(args=[], returncode=1, stdout="", stderr="interpreter missing")

    monkeypatch.setattr("gil_evaluator.subprocess_runner.subprocess.run", fake_run)

    results = run_runtime_in_subprocess(
        runtime="py313t",
        executable="python3.13t",
        config=SubprocessConfig(timeout_sec=1.0, repeat_perf=1, repeat_non_perf=2),
        selected_libraries=None,
    )

    assert len(results) == 1
    assert results[0].status is ScenarioStatus.ERROR
    assert results[0].error_type == "RuntimeExecutionError"
