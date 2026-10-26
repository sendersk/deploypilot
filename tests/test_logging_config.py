"""Tests for logging configuration."""

import logging

from deploypilot.logging_config import configure_logging


def test_configure_logging_sets_requested_level() -> None:
    """Set the root logger to the requested logging level."""
    configure_logging(logging.WARNING)

    assert logging.getLogger().level == logging.WARNING
