# Agent Roles

This directory contains role-oriented templates for orchestrating evaluator workflows.

## Roles

- `planner.yaml`: translates requests into concrete tasks and acceptance criteria.
- `evaluator.yaml`: runs runtime/library scenario batteries and records evidence.
- `reporter.yaml`: computes compatibility tiers and writes summaries/artifacts.

## Recommended Orchestration

1. `planner`
2. `evaluator`
3. `reporter`

## Input/Output Contract

Evaluator output records should include:
- `library`
- `scenario_id`
- `runtime`
- `status`
- `duration_ms`
- `error_type`
- `error_message`
- `metadata`

Reporter output should include:
- `compatibility_tier`
- `failure_count`
- `crash_count`
- `perf_regression_pct`
- `notes`

## Dry-Run Example

1. Planner receives: "Add support for redis-py compatibility checks."
2. Planner emits tasks and success criteria.
3. Evaluator runs redis adapter scenarios across `py312` and `py313t`.
4. Reporter emits verdict + JSON artifact for CI use.
