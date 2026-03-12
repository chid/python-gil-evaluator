from __future__ import annotations

import argparse
import json
from pathlib import Path

from gil_evaluator.models import Report, ScenarioResult
from gil_evaluator.reporting import render_markdown_summary, write_report_json
from gil_evaluator.scoring import score_results


def _load_results(path: Path) -> list[ScenarioResult]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [ScenarioResult.from_dict(item) for item in payload.get("results", [])]


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate runtime reports into one combined report.")
    parser.add_argument("--inputs", required=True, help="Comma-separated report JSON file paths.")
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--markdown-out", required=True, type=Path)
    parser.add_argument("--perf-threshold", type=float, default=20.0)
    args = parser.parse_args()

    input_paths = [Path(item.strip()) for item in args.inputs.split(",") if item.strip()]
    all_results: list[ScenarioResult] = []
    runtimes: list[str] = []

    for path in input_paths:
        results = _load_results(path)
        all_results.extend(results)
        for result in results:
            if result.runtime not in runtimes:
                runtimes.append(result.runtime)

    report = Report(
        results=all_results,
        verdicts=score_results(all_results, perf_threshold_pct=args.perf_threshold),
        runtimes=runtimes,
        perf_threshold_pct=args.perf_threshold,
        history_regressions=[],
    )

    write_report_json(report, args.json_out)
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_markdown_summary(report), encoding="utf-8")


if __name__ == "__main__":
    main()
