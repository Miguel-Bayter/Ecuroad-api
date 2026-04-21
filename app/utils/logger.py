import logging
import sys

import structlog

from config import get_settings


def _configure_structlog() -> None:
    settings = get_settings()
    is_production = settings.LOG_LEVEL.lower() not in ("debug", "info") or False

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )


_configured = False


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    global _configured
    if not _configured:
        _configure_structlog()
        _configured = True
    return structlog.get_logger(name)
