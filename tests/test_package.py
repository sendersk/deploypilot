"""Smoke tests for the DeployPilot package."""

from importlib import import_module
from types import ModuleType


def test_package_can_be_imported() -> None:
    """Verify that the main package can be imported successfully."""
    package: ModuleType = import_module("deploypilot")

    assert package.__name__ == "deploypilot"
    assert package.__file__ is not None
