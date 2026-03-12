# Python GIL Evaluator

`python-gil-evaluator` tests library behavior across traditional GIL and free-threaded Python runtimes.

It includes:
- Adapter-based scenario framework.
- Functional, stress, and performance scenarios.
- Tiered verdicts: `Compatible`, `Warning`, `Incompatible`.
- Flaky/deadlock-oriented heuristics and confidence scoring.
- CLI summary plus JSON artifact output.
- Baseline history tracking with automatic regression detection.

## Runtime Targets

- `py312` (baseline GIL runtime)
- `py313t` (free-threaded runtime)

By default, runtime labels map to executables:
- `py312 -> python3.12`
- `py313t -> python3.13t`

Override mappings with `--runtime-exec`.

## Quick Start

```bash
uv sync --extra dev
uv run gil-eval --json-out artifacts/gil_eval_report.json
```

Run selected libraries:

```bash
uv run gil-eval --libraries numpy,pandas,orjson
```

Run the priority top-10 roadmap list:

```bash
uv run gil-eval --libraries-file configs/priority_libraries.txt
```

Pin runtime executables:

```bash
uv run gil-eval --runtime-exec py312=/usr/bin/python3.12,py313t=/opt/python3.13t/bin/python
```

Disable history tracking for a one-off run:

```bash
uv run gil-eval --disable-history
```

Debug with in-process runtime execution:

```bash
uv run gil-eval --in-process
```

Load external plugin adapters:

```bash
uv run gil-eval --plugin your_pkg.gil_plugins:RedisClusterAdapter
```

Validate plugin contracts without running scenarios:

```bash
uv run gil-eval --plugin your_pkg.gil_plugins:RedisClusterAdapter --validate-plugins
```

Run by curated profile:

```bash
uv run gil-eval --profile data
uv run gil-eval --profile web
uv run gil-eval --profile infra
uv run gil-eval --profile priority
```

Compare against a previous report and include trend metrics:

```bash
uv run gil-eval --compare-with artifacts/previous_report.json --trend-window 10
```

## Built-in Adapters

- `threading_baseline`
- `numpy`
- `pandas`
- `httpx`
- `sqlalchemy`
- `orjson`
- `pydantic`
- `polars`
- `fastapi`
- `redis`
- `grpcio`

Missing dependencies are reported as `SKIPPED` with reason `dependency_missing`.

## Optional Dependency Groups

```bash
uv sync --extra scientific
uv sync --extra web
uv sync --extra infra
uv sync --extra all
```

## Verdict and Heuristics

- `Incompatible`: critical failures in `py313t` (`ERROR`, `TIMEOUT`, `FAILURE`).
- `Warning`: no critical failures, but performance regression `>= threshold` (default `20%`).
- `Compatible`: no critical failures and no major perf regression.

Additional signals:
- `flaky_case_count`: scenarios with mixed outcomes across retries.
- `timeout_count`: timeout/deadlock risk indicator.
- `confidence_score`: 0.0-1.0 reliability score derived from failures/flaky outcomes.
- `adapter_metadata`: domain/risk/workload metadata for each library.
- `regression_deltas`: explicit diff against `--compare-with` report.
- `trend_metrics`: rolling summary from recent history snapshots.

## History Tracking

Each run can compare with the previous snapshot in `artifacts/history.json`.
Regression detection flags:
- compatibility tier worsening
- performance regression delta increase (>= 10 percentage points)

## Pre-commit

Install hooks:

```bash
uv run pre-commit install
```

Run all hooks:

```bash
uv run pre-commit run --all-files
```

## Extending the Framework

1. Add a new adapter in `src/gil_evaluator/adapters.py`.
2. Return `Case` objects with stable `case_id` values.
3. Register adapter in `default_adapters()`.
4. Or provide external plugins via entry points group `gil_evaluator.adapters` or `--plugin`.
5. Add tests for runner/scoring/history impacts.

## Project Docs

- Implementation plan: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md)
- Priority roadmap: [`docs/PRIORITY_LIBRARY_ROADMAP.md`](docs/PRIORITY_LIBRARY_ROADMAP.md)
- Contributor/agent workflow rules: [`AGENTS.md`](AGENTS.md)
- Role-oriented agent configs: [`agents/README.md`](agents/README.md)
