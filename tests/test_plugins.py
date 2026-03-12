from __future__ import annotations

import pytest

from gil_evaluator.plugins import load_plugin_adapters


def test_load_plugin_adapter_from_spec() -> None:
    adapters = load_plugin_adapters(["tests.fixtures.plugin_adapter:DemoPluginAdapter"])
    assert len(adapters) == 1
    assert adapters[0].name == "demo_plugin"


def test_plugin_spec_format_validation() -> None:
    with pytest.raises(ValueError):
        load_plugin_adapters(["tests.fixtures.plugin_adapter"])
