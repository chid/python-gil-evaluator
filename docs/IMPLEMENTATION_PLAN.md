# Implementation Plan: Python GIL Compatibility Evaluator

## Summary

Build and maintain a framework that evaluates Python library readiness for a free-threaded runtime by comparing behavior and performance across `py312` and `py313t`.

## Milestone 1: Foundation

- Create a `uv` + `pytest` project layout.
- Implement evaluation core:
  - Adapter protocol for libraries.
  - Scenario execution engine.
  - Functional/stress/perf case model.
- Implement reporting:
  - CLI summary.
  - JSON artifact export.
- Implement tiered scoring:
  - `Incompatible`, `Warning`, `Compatible`.

Acceptance criteria:
- `uv run gil-eval` executes and emits JSON report.
- Missing dependencies are reported as `SKIPPED` (not silent).
- Score classification is deterministic for the same inputs.

## Milestone 2: Broad Initial Battery

- Include built-in adapters for:
  - `numpy`
  - `pandas`
  - `httpx`
  - `sqlalchemy`
  - `threading_baseline`
- Provide meaningful functional and stress checks per adapter.
- Provide at least one performance scenario for adapters where useful.

Acceptance criteria:
- Built-in adapters run without code changes when dependencies are installed.
- Each adapter has stable case IDs and appears in report output.

## Milestone 3: Quality Gates

- Add tests for:
  - Scoring thresholds and tier transitions.
  - Runner behavior for missing dependencies.
  - Perf repeat aggregation.
- Add lint/test commands to contributor workflow.

Acceptance criteria:
- `uv run pytest` passes.
- Threshold boundary behavior (`20%`) is explicitly covered by tests.

## Milestone 4: CI Automation

- Add GitHub Actions Ubuntu workflow to run tests and emit evaluation artifacts.
- Support scheduled/manual evaluator runs.

Acceptance criteria:
- CI uploads report artifact for evaluator job.
- Failing tests block merges.

## Public Interfaces

- `LibraryAdapter` contract:
  - `name`
  - `import_check()`
  - `functional_cases()`
  - `stress_cases()`
  - `perf_cases()`
- `ScenarioResult` fields:
  - `library`, `scenario_id`, `runtime`, `status`, `duration_ms`, `error_type`, `error_message`, `metadata`
- `LibraryVerdict` fields:
  - `compatibility_tier`, `failure_count`, `crash_count`, `perf_regression_pct`, `notes`

## Defaults and Assumptions

- Runtime matrix defaults to `py312,py313t`.
- Performance threshold default is `20%` slowdown for `Warning`.
- Dependency management uses curated optional groups.
- CLI and JSON outputs are both required.

## Definition of Done

- Framework runs end-to-end with built-in adapters.
- JSON schema and tier logic are tested.
- README explains setup, execution, and interpretation.
- `AGENTS.md` + `agents/*` provide clear operational guidance.
