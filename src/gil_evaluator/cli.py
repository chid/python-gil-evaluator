from __future__ import annotations

import argparse
from pathlib import Path

from .models import Report
from .reporting import render_summary, write_report_json
from .runner import RunnerConfig, run_runtime
from .scoring import score_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate library behavior under GIL and free-threaded runtimes.")
    parser.add_argument(
        "--runtimes",
        default="py312,py313t",
        help="Comma-separated runtime labels. Defaults to py312,py313t.",
    )
    parser.add_argument(
        "--libraries",
        default="",
        help="Comma-separated library names to include (default: all known adapters).",
    )
    parser.add_argument("--perf-threshold", type=float, default=20.0)
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--repeat-perf", type=int, default=3)
    parser.add_argument("--json-out", type=Path, default=Path("artifacts/gil_eval_report.json"))
    parser.add_argument("--no-summary", action="store_true", help="Suppress terminal summary output.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    runtimes = [item.strip() for item in args.runtimes.split(",") if item.strip()]
    selected = {item.strip() for item in args.libraries.split(",") if item.strip()} or None

    all_results = []
    for runtime in runtimes:
        config = RunnerConfig(runtime=runtime, timeout_sec=args.timeout_sec, repeat_perf=args.repeat_perf)
        all_results.extend(run_runtime(config=config, selected_libraries=selected))

    report = Report(
        results=all_results,
        verdicts=score_results(all_results, perf_threshold_pct=args.perf_threshold),
        runtimes=runtimes,
        perf_threshold_pct=args.perf_threshold,
    )

    write_report_json(report, args.json_out)

    if not args.no_summary:
        print(render_summary(report))
        print(f"\nJSON report: {args.json_out}")


if __name__ == "__main__":
    main()
