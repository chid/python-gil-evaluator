from __future__ import annotations

import importlib
from importlib.metadata import entry_points
from typing import Any

from .adapters import LibraryAdapter


def load_plugin_adapters(specs: list[str] | None = None) -> list[LibraryAdapter]:
    adapters: list[LibraryAdapter] = []
    adapters.extend(_load_entrypoint_adapters())
    for spec in specs or []:
        adapters.append(_load_from_spec(spec))
    return adapters


def validate_plugin_specs(specs: list[str]) -> list[dict[str, str]]:
    validations: list[dict[str, str]] = []
    for spec in specs:
        adapter = _load_from_spec(spec)
        validations.append({"spec": spec, "adapter_name": adapter.name, "status": "ok"})
    return validations


def _load_entrypoint_adapters() -> list[LibraryAdapter]:
    loaded: list[LibraryAdapter] = []
    group_entries = entry_points(group="gil_evaluator.adapters")
    for ep in group_entries:
        loaded.append(_normalize_adapter_obj(ep.load()))
    return loaded


def _load_from_spec(spec: str) -> LibraryAdapter:
    if ":" not in spec:
        raise ValueError(
            "Invalid plugin spec. Expected format 'module.path:AdapterClassOrFactory'."
        )
    module_name, symbol = spec.split(":", 1)
    module = importlib.import_module(module_name)
    obj = getattr(module, symbol)
    return _normalize_adapter_obj(obj)


def _normalize_adapter_obj(obj: Any) -> LibraryAdapter:
    candidate = obj() if callable(obj) else obj
    required = ["name", "import_check", "functional_cases", "stress_cases", "perf_cases"]
    missing = [attr for attr in required if not hasattr(candidate, attr)]
    if missing:
        raise TypeError(f"Plugin adapter missing required attributes: {', '.join(missing)}")
    return candidate
