from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import PROFILE_LIBRARY_MAP, libraries_for_profile
from .history import append_history, build_trend_metrics, compare_with_latest, compare_with_report
from .models import Report
from .plugins import load_plugin_adapters, validate_plugin_specs
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
    parser.add_argument(
        "--libraries-file",
        type=Path,
        default=None,
        help="Path to newline-delimited library names. Merged with --libraries.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_LIBRARY_MAP.keys()),
        default=None,
        help="Optional curated library profile to run (data/web/infra/priority).",
    )
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Plugin adapter spec module.path:AdapterClassOrFactory. Can be repeated.",
    )
    parser.add_argument(
        "--validate-plugins",
        action="store_true",
        help="Validate plugin specs and exit without executing evaluation scenarios.",
    )
    parser.add_argument("--perf-threshold", type=float, default=20.0)
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--repeat-perf", type=int, default=3)
    parser.add_argument("--repeat-non-perf", type=int, default=2)
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/gil_eval_report.json"))
    parser.add_argument("--history-file", type=Path, default=Path("artifacts/history.json"))
    parser.add_argument(
        "--compare-with",
        type=Path,
        default=None,
        help="Optional previous report JSON path for explicit regression delta comparison.",
    )
    parser.add_argument(
        "--trend-window",
        type=int,
        default=5,
        help="History snapshot window used to compute trend metrics (default: 5).",
    )
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

    if args.validate_plugins:
        validations = validate_plugin_specs(args.plugin)
        print(json.dumps({"plugins": validations}, indent=2))
        return

    runtimes = [item.strip() for item in args.runtimes.split(",") if item.strip()]
    selected = {item.strip() for item in args.libraries.split(",") if item.strip()}
    if args.libraries_file:
        lines = args.libraries_file.read_text(encoding="utf-8").splitlines()
        selected.update(
            item.strip() for item in lines if item.strip() and not item.strip().startswith("#")
        )
    if args.profile:
        selected.update(libraries_for_profile(args.profile))

    selected_libraries = selected or None
    plugin_adapters = load_plugin_adapters(args.plugin)
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
            all_results.extend(
                run_runtime(
                    config=config,
                    selected_libraries=selected_libraries,
                    plugin_adapters=plugin_adapters,
                )
            )
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
                selected_libraries=selected_libraries,
                plugin_specs=args.plugin,
            )
        )

    verdicts = score_results(all_results, perf_threshold_pct=args.perf_threshold)
    history_regressions: list[dict] = []
    trend_metrics: dict[str, dict] = {}
    if not args.disable_history:
        history_regressions = compare_with_latest(args.history_file, verdicts)
        trend_metrics = build_trend_metrics(args.history_file, verdicts, args.trend_window)
        append_history(args.history_file, verdicts, runtimes, args.perf_threshold)

    regression_deltas: list[dict] = []
    if args.compare_with:
        regression_deltas = compare_with_report(args.compare_with, verdicts)

    adapter_metadata = _collect_adapter_metadata(all_results)

    report = Report(
        results=all_results,
        verdicts=verdicts,
        runtimes=runtimes,
        profile=args.profile,
        perf_threshold_pct=args.perf_threshold,
        history_regressions=history_regressions,
        regression_deltas=regression_deltas,
        trend_metrics=trend_metrics,
        adapter_metadata=adapter_metadata,
    )

    write_report_json(report, args.json_out)

    if not args.no_summary:
        print(render_summary(report))
        if history_regressions:
            print("\nHistory regressions:")
            for reg in history_regressions:
                print(f"- {reg}")
        if regression_deltas:
            print("\nComparison deltas:")
            for reg in regression_deltas:
                print(f"- {reg}")
        print(f"\nJSON report: {args.json_out}")


def _collect_adapter_metadata(results: list) -> dict[str, dict]:
    metadata: dict[str, dict] = {}
    for result in results:
        adapter_meta = result.metadata.get("adapter_metadata")
        if isinstance(adapter_meta, dict):
            metadata[result.library] = adapter_meta
    return metadata


if __name__ == "__main__":
    main()
