# Priority Library Roadmap

This roadmap defines the first 10 libraries to deepen for no-GIL compatibility evaluation.

## Priority Top 10

1. `numpy`
2. `pandas`
3. `sqlalchemy`
4. `httpx`
5. `pydantic`
6. `fastapi`
7. `polars`
8. `redis`
9. `grpcio`
10. `orjson`

## Deep Scenario Goals

For each priority library, add:
- 3 functional scenarios covering core API invariants.
- 2 stress scenarios with parallel read/write/encode/decode activity.
- 1 perf scenario with stable workload and repeatability.
- 1 failure-injection scenario (timeouts, retries, cancellations, invalid input).

## Success Criteria by Library

- No `ERROR`/`TIMEOUT` under `py313t` in the deep suite.
- `confidence_score >= 0.90`.
- No perf warning (`<20%` regression) for at least one representative workload.

## Rollout Order

- Wave 1: `numpy`, `pandas`, `sqlalchemy`, `httpx`
- Wave 2: `pydantic`, `fastapi`, `polars`
- Wave 3: `redis`, `grpcio`, `orjson`

## CI Execution Policy

- PRs: run priority list via `configs/priority_libraries.txt`.
- Scheduled weekly: run full adapter battery.
- Monthly: raise scenario depth target for next 2 libraries.
