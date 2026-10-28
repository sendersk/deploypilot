"""Tests for logging configuration."""

import logging

import pytest

from deploypilot.logging_config import configure_logging


def test_configure_logging_sets_requested_level() -> None:
    """Set the root logger to the requested logging level."""
    configure_logging("WARNING")

    assert logging.getLogger().level == logging.WARNING


@pytest.mark.parametrize(
    ("level_name", "expected_level"),
    [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
    ],
)
def test_configure_logging_supports_all_levels(
    level_name: str,
    expected_level: int,
) -> None:
    """Support every documented logging level."""
    configure_logging(level_name)

    assert logging.getLogger().level == expected_level


def test_configure_logging_normalizes_lowercase_level() -> None:
    """Accept lowercase level names."""
    configure_logging("debug")

    assert logging.getLogger().level == logging.DEBUG


def test_configure_logging_rejects_unsupported_level() -> None:
    """Reject unsupported logging levels."""
    with pytest.raises(ValueError, match="Unsupported log level"):
        configure_logging("TRACE")
