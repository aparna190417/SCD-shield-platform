import logging

from shield.config.logging import ContextFilter, configure_logging


def test_context_filter_adds_missing_context_fields() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    ContextFilter().filter(record)

    assert record.incident_id == "-"
    assert record.request_id == "-"


def test_context_filter_preserves_existing_context_fields() -> None:
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None,
    )

    record.incident_id = "INC-001"
    record.request_id = "REQ-001"

    ContextFilter().filter(record)

    assert record.incident_id == "INC-001"
    assert record.request_id == "REQ-001"


def test_configure_logging_sets_requested_level() -> None:
    configure_logging(level="DEBUG")

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG


def test_configure_logging_normalizes_level() -> None:
    configure_logging(level="debug")

    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG