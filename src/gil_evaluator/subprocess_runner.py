from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass

from .models import ScenarioResult, ScenarioStatus

DEFAULT_RUNTIME_EXECUTABLES = {
    "py312": "python3.12",
    "py313t": "python3.13t",
}


@dataclass(slots=True)
class SubprocessConfig:
    timeout_sec: float
    repeat_perf: int
    repeat_non_perf: int


def parse_runtime_exec_map(raw: str) -> dict[str, str]:
    if not raw.strip():
        return {}

    mapping: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                "Invalid --runtime-exec mapping. Expected format runtime=python_executable."
            )
        runtime, executable = item.split("=", 1)
        runtime = runtime.strip()
        executable = executable.strip()
        if not runtime or not executable:
            raise ValueError(
                "Invalid --runtime-exec mapping. Expected format runtime=python_executable."
            )
        mapping[runtime] = executable
    return mapping


def resolve_runtime_executable(runtime: str, overrides: dict[str, str]) -> str:
    if runtime in overrides:
        return overrides[runtime]
    return DEFAULT_RUNTIME_EXECUTABLES.get(runtime, runtime)


def run_runtime_in_subprocess(
    runtime: str,
    executable: str,
    config: SubprocessConfig,
    selected_libraries: set[str] | None,
    plugin_specs: list[str] | None = None,
) -> list[ScenarioResult]:
    command = [
        executable,
        "-m",
        "gil_evaluator.runtime_worker",
        "--runtime",
        runtime,
        "--timeout-sec",
        str(config.timeout_sec),
        "--repeat-perf",
        str(config.repeat_perf),
        "--repeat-non-perf",
        str(config.repeat_non_perf),
    ]

    if selected_libraries:
        command.extend(["--libraries", ",".join(sorted(selected_libraries))])
    for spec in plugin_specs or []:
        command.extend(["--plugin", spec])

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "subprocess failed"
        return [
            ScenarioResult(
                library="runtime",
                scenario_id=f"{runtime}.bootstrap",
                runtime=runtime,
                status=ScenarioStatus.ERROR,
                duration_ms=0.0,
                error_type="RuntimeExecutionError",
                error_message=message,
                metadata={"executable": executable, "command": command},
            )
        ]

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return [
            ScenarioResult(
                library="runtime",
                scenario_id=f"{runtime}.bootstrap",
                runtime=runtime,
                status=ScenarioStatus.ERROR,
                duration_ms=0.0,
                error_type="RuntimeExecutionError",
                error_message=f"Invalid JSON from runtime worker: {exc}",
                metadata={"executable": executable, "command": command},
            )
        ]

    return [ScenarioResult.from_dict(item) for item in payload]
