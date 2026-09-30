import logging
import logging.config
from typing import Any

DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(message)s | incident_id=%(incident_id)s | request_id=%(request_id)s"
)


class ContextFilter(logging.Filter):
    """Ensure correlation fields are available on every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "incident_id"):
            record.incident_id = "-"
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def configure_logging(
    *,
    level: str = "INFO",
    log_format: str = DEFAULT_LOG_FORMAT,
) -> None:
    """Configure application-wide logging."""

    normalized_level = level.upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "context": {
                    "()": ContextFilter,
                },
            },
            "formatters": {
                "standard": {
                    "format": log_format,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": normalized_level,
                    "formatter": "standard",
                    "filters": ["context"],
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": normalized_level,
                "handlers": ["console"],
            },
        }
    )


def configure_logging_from_settings(settings: Any) -> None:
    """Configure logging using application settings."""

    configure_logging(
        level=settings.log_level,
    )