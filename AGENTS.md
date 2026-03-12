# AGENTS Guide

This repository evaluates Python library behavior under GIL and free-threaded runtime targets.

## Objectives

- Produce repeatable compatibility evidence.
- Keep scenario logic deterministic and debuggable.
- Surface failures with machine-readable and human-readable outputs.

## Architecture Map

- `src/gil_evaluator/adapters.py`: library adapters and built-in test batteries.
- `src/gil_evaluator/runner.py`: scenario execution with timeout handling.
- `src/gil_evaluator/scoring.py`: verdict policy and regression thresholds.
- `src/gil_evaluator/reporting.py`: CLI summary and JSON report writing.
- `tests/`: unit tests for scoring and runtime behavior.

## Core Commands

```bash
uv sync --extra dev
uv run pytest
uv run gil-eval --json-out artifacts/gil_eval_report.json
uv run gil-eval --libraries numpy,pandas
```

Optional dependency groups:

```bash
uv sync --extra scientific
uv sync --extra web
uv sync --extra all
```

## Agent Operating Rules

- Never silently ignore missing dependencies; report `SKIPPED` with reason.
- Maintain stable `scenario_id` names to protect report consumers.
- Keep threshold-based policies centralized in `scoring.py`.
- Do not introduce non-deterministic tests (no random without fixed seed).
- Prefer adapter-specific cases over hardcoded behavior in runner/scoring.

## Adding a New Library Adapter

1. Add adapter class in `adapters.py` with full contract methods.
2. Add at least one functional case and one stress or perf case.
3. Register adapter in `default_adapters()`.
4. Add or update tests validating expected statuses/verdict behavior.
5. Update README if new optional dependency group is introduced.

## Report Quality Requirements

- Required result fields: `library`, `scenario_id`, `runtime`, `status`, `duration_ms`.
- Required verdict fields: `compatibility_tier`, `failure_count`, `crash_count`.
- Error fields must be set for non-success statuses.
- JSON report must remain parseable and stable for CI consumers.

## Failure Handling

- Use `TIMEOUT` when scenario exceeds configured limit.
- Use `ERROR` for raised exceptions.
- Use `SKIPPED` only for clear non-execution reasons (e.g., missing dependency).
- Any critical error in `py313t` must drive `Incompatible` verdict.
