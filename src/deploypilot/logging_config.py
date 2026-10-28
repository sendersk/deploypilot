"""Configure application logging."""

import logging

SUPPORTED_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def configure_logging(level: str = "INFO") -> None:
    """Configure console logging using a supported level name."""
    normalized_level = level.strip().upper()

    if normalized_level not in SUPPORTED_LOG_LEVELS:
        supported = ", ".join(SUPPORTED_LOG_LEVELS)
        raise ValueError(
            f"Unsupported log level '{level}'. Choose one of: {supported}."
        )

    logging.basicConfig(
        level=getattr(logging, normalized_level),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        force=True,
    )
