"""Configure application logging."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure consistent console logging for DeployPilot."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
