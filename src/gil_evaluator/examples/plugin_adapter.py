from __future__ import annotations

from gil_evaluator.cases import Case, CaseType


class DemoPluginAdapter:
    name = "demo_plugin"

    def import_check(self) -> tuple[bool, str | None]:
        return True, None

    def functional_cases(self) -> list[Case]:
        return [Case("demo_plugin.functional", CaseType.FUNCTIONAL, lambda: {"ok": 1})]

    def stress_cases(self) -> list[Case]:
        return []

    def perf_cases(self) -> list[Case]:
        return []
