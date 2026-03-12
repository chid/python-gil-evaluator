from __future__ import annotations

import json
from pathlib import Path

from .models import CompatibilityTier, Report


def write_report_json(report: Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def render_summary(report: Report) -> str:
    lines: list[str] = []
    lines.append("GIL Compatibility Evaluation")
    lines.append(f"Runtimes: {', '.join(report.runtimes)}")
    lines.append(f"Performance warning threshold: {report.perf_threshold_pct:.2f}%")
    lines.append("")

    for verdict in sorted(report.verdicts, key=lambda item: item.library):
        icon = _tier_icon(verdict.compatibility_tier)
        perf = (
            f"{verdict.perf_regression_pct:.2f}%"
            if verdict.perf_regression_pct is not None
            else "n/a"
        )
        lines.append(
            f"{icon} {verdict.library}: {verdict.compatibility_tier.value} "
            f"(failures={verdict.failure_count}, crashes={verdict.crash_count}, perf_reg={perf})"
        )

    return "\n".join(lines)


def render_markdown_summary(report: Report) -> str:
    lines: list[str] = []
    lines.append("## GIL Compatibility Summary")
    lines.append("")
    lines.append(f"- Runtimes: `{', '.join(report.runtimes)}`")
    lines.append(f"- Perf warning threshold: `{report.perf_threshold_pct:.2f}%`")
    lines.append("")
    lines.append(
        "| Library | Tier | Failures | Crashes | Flaky | Timeouts | Confidence | Perf Regression |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for verdict in sorted(report.verdicts, key=lambda item: item.library):
        perf = (
            f"{verdict.perf_regression_pct:.2f}%"
            if verdict.perf_regression_pct is not None
            else "n/a"
        )
        lines.append(
            f"| `{verdict.library}` | {verdict.compatibility_tier.value} | "
            f"{verdict.failure_count} | {verdict.crash_count} | "
            f"{verdict.flaky_case_count} | {verdict.timeout_count} | "
            f"{verdict.confidence_score:.3f} | {perf} |"
        )
    if report.history_regressions:
        lines.append("")
        lines.append("### History Regressions")
        for reg in report.history_regressions:
            lines.append(f"- `{reg}`")
    return "\n".join(lines)


def _tier_icon(tier: CompatibilityTier) -> str:
    if tier is CompatibilityTier.COMPATIBLE:
        return "PASS"
    if tier is CompatibilityTier.WARNING:
        return "WARN"
    return "FAIL"
