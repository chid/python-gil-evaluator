from gil_evaluator.adapters import adapter_metadata_for_library, libraries_for_profile


def test_libraries_for_profile_priority() -> None:
    libs = libraries_for_profile("priority")
    assert "numpy" in libs
    assert "grpcio" in libs


def test_adapter_metadata_defaults_for_unknown() -> None:
    metadata = adapter_metadata_for_library("unknown-lib")
    assert metadata["domain"] == "unknown"
    assert metadata["risk_level"] == "unknown"
