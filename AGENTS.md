# AGENTS Guide

This repository evaluates Python library behavior under GIL and free-threaded runtimes.

## Objectives

- Produce repeatable compatibility evidence.
- Detect critical failures, flaky behavior, and deadlock risk.
- Track historical regressions over time.

## Architecture Map

- `src/gil_evaluator/adapters.py`: library adapters and built-in batteries.
- `src/gil_evaluator/runner.py`: scenario execution with retries + timeout handling.
- `src/gil_evaluator/runtime_worker.py`: single-runtime worker entrypoint.
- `src/gil_evaluator/subprocess_runner.py`: runtime-to-interpreter subprocess orchestration.
- `src/gil_evaluator/scoring.py`: tier policy + confidence/flaky/deadlock heuristics.
- `src/gil_evaluator/history.py`: snapshot append + historical regression comparison.
- `src/gil_evaluator/reporting.py`: CLI summary and JSON report writing.

## Core Commands

```bash
uv sync --extra dev
uv run pytest
uv run gil-eval --json-out artifacts/gil_eval_report.json
uv run gil-eval --runtime-exec py312=python3.12,py313t=python3.13t
uv run pre-commit install
uv run pre-commit run --all-files
```

Optional stacks:

```bash
uv sync --extra scientific
uv sync --extra web
uv sync --extra infra
uv sync --extra all
```

## Operating Rules

- Never silently ignore missing dependencies; use `SKIPPED` with reason.
- Keep `scenario_id` stable to preserve report compatibility.
- Keep tier logic and heuristics centralized in `scoring.py`.
- Keep history comparison behavior centralized in `history.py`.
- Avoid non-deterministic tests unless explicitly controlled.

## Adding New Adapters

1. Implement adapter contract methods in `adapters.py`.
2. Include at least one functional and one stress/perf scenario.
3. Register adapter in `default_adapters()`.
4. Add tests for runner + scoring behavior.
5. Update README and optional dependency groups if needed.

## Quality Requirements

- Scenario records must include runtime, status, duration, and metadata.
- Non-success statuses must include `error_type` and diagnostic message.
- Verdict records must include compatibility tier + heuristic metrics.
- JSON reports must remain stable and machine-readable for CI.
