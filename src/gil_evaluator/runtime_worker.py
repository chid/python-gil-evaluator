from __future__ import annotations

import argparse
import json

from .plugins import load_plugin_adapters
from .runner import RunnerConfig, run_runtime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute evaluator scenarios for one runtime.")
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--libraries", default="")
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--repeat-perf", type=int, default=3)
    parser.add_argument("--repeat-non-perf", type=int, default=2)
    parser.add_argument(
        "--plugin",
        action="append",
        default=[],
        help="Plugin adapter spec module.path:AdapterClassOrFactory. Can be repeated.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    selected = {item.strip() for item in args.libraries.split(",") if item.strip()} or None
    plugin_adapters = load_plugin_adapters(args.plugin)

    results = run_runtime(
        config=RunnerConfig(
            runtime=args.runtime,
            timeout_sec=args.timeout_sec,
            repeat_perf=args.repeat_perf,
            repeat_non_perf=args.repeat_non_perf,
        ),
        selected_libraries=selected,
        plugin_adapters=plugin_adapters,
    )

    print(json.dumps([result.to_dict() for result in results]))


if __name__ == "__main__":
    main()
