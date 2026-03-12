from __future__ import annotations

import argparse
from pathlib import Path

from .history import append_history, compare_with_latest
from .models import Report
from .reporting import render_summary, write_report_json
from .runner import RunnerConfig, run_runtime
from .scoring import score_results
from .subprocess_runner import (
    SubprocessConfig,
    parse_runtime_exec_map,
    resolve_runtime_executable,
    run_runtime_in_subprocess,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate library behavior under GIL and free-threaded runtimes."
    )
    parser.add_argument(
        "--runtimes",
        default="py312,py313t",
        help="Comma-separated runtime labels. Defaults to py312,py313t.",
    )
    parser.add_argument(
        "--runtime-exec",
        default="",
        help=(
            "Optional runtime->python mapping, e.g. py312=python3.12,py313t=python3.13t. "
            "Unspecified runtimes default to py312->python3.12, "
            "py313t->python3.13t, otherwise runtime label."
        ),
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Run scenarios in-process instead of spawning runtime-specific executables.",
    )
    parser.add_argument(
        "--libraries",
        default="",
        help="Comma-separated library names to include (default: all known adapters).",
    )
    parser.add_argument("--perf-threshold", type=float, default=20.0)
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--repeat-perf", type=int, default=3)
    parser.add_argument("--repeat-non-perf", type=int, default=2)
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/gil_eval_report.json"))
    parser.add_argument("--history-file", type=Path, default=Path("artifacts/history.json"))
    parser.add_argument(
        "--disable-history",
        action="store_true",
        help="Disable history append/comparison.",
    )
    parser.add_argument(
        "--no-summary", action="store_true", help="Suppress terminal summary output."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    runtimes = [item.strip() for item in args.runtimes.split(",") if item.strip()]
    selected = {item.strip() for item in args.libraries.split(",") if item.strip()} or None
    runtime_overrides = parse_runtime_exec_map(args.runtime_exec)

    all_results = []
    for runtime in runtimes:
        if args.in_process:
            config = RunnerConfig(
                runtime=runtime,
                timeout_sec=args.timeout_sec,
                repeat_perf=args.repeat_perf,
                repeat_non_perf=args.repeat_non_perf,
            )
            all_results.extend(run_runtime(config=config, selected_libraries=selected))
            continue

        executable = resolve_runtime_executable(runtime, runtime_overrides)
        all_results.extend(
            run_runtime_in_subprocess(
                runtime=runtime,
                executable=executable,
                config=SubprocessConfig(
                    timeout_sec=args.timeout_sec,
                    repeat_perf=args.repeat_perf,
                    repeat_non_perf=args.repeat_non_perf,
                ),
                selected_libraries=selected,
            )
        )

    verdicts = score_results(all_results, perf_threshold_pct=args.perf_threshold)
    regressions: list[dict] = []
    if not args.disable_history:
        regressions = compare_with_latest(args.history_file, verdicts)
        append_history(args.history_file, verdicts, runtimes, args.perf_threshold)

    report = Report(
        results=all_results,
        verdicts=verdicts,
        runtimes=runtimes,
        perf_threshold_pct=args.perf_threshold,
        history_regressions=regressions,
    )

    write_report_json(report, args.json_out)

    if not args.no_summary:
        print(render_summary(report))
        if regressions:
            print("\nHistory regressions:")
            for reg in regressions:
                print(f"- {reg}")
        print(f"\nJSON report: {args.json_out}")


if __name__ == "__main__":
    main()
