# Python GIL Evaluator

`python-gil-evaluator` is a framework for testing whether Python libraries behave correctly under a traditional GIL runtime and a free-threaded runtime.

It provides:
- A reusable adapter-based evaluation framework.
- Functional, stress, and performance scenarios.
- Tiered verdicts (`Compatible`, `Warning`, `Incompatible`).
- CLI output plus machine-readable JSON reports.

## Runtime Targets

- `py312` (baseline GIL runtime)
- `py313t` (free-threaded runtime label)

The default run compares both labels. For real-world validation, execute under actual Python interpreters for each label in CI.

## Quick Start

```bash
uv sync --extra dev
uv run gil-eval --json-out artifacts/gil_eval_report.json
```

Run only selected libraries:

```bash
uv run gil-eval --libraries numpy,pandas
```

Set custom policy/limits:

```bash
uv run gil-eval --perf-threshold 20 --timeout-sec 10 --repeat-perf 5
```

## Dependency Groups

Install optional stacks as needed:

```bash
uv sync --extra scientific
uv sync --extra web
uv sync --extra all
```

If a library dependency is missing, scenarios are marked `SKIPPED` with reason `dependency_missing`.

## Verdict Rules

- `Incompatible`: any critical failure in `py313t` (errors/timeouts/failures).
- `Warning`: no critical failures, but max perf slowdown is `>= threshold` (default `20%`).
- `Compatible`: no critical failures and no major regression.

## JSON Report Shape

Each scenario result includes:
- `library`
- `scenario_id`
- `runtime`
- `status`
- `duration_ms`
- `error_type`
- `error_message`
- `metadata`

Each library verdict includes:
- `compatibility_tier`
- `failure_count`
- `crash_count`
- `perf_regression_pct`
- `notes`

## Extending the Framework

1. Implement a new adapter in `src/gil_evaluator/adapters.py` with:
   - `import_check()`
   - `functional_cases()`
   - `stress_cases()`
   - `perf_cases()`
2. Return `Case` objects with stable `case_id` values.
3. Add adapter to `default_adapters()`.
4. Add unit/integration tests.

## Project Docs

- Implementation plan: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)
- Contributor/agent workflow rules: [`AGENTS.md`](AGENTS.md)
- Role-oriented agent configs: [`agents/README.md`](agents/README.md)
