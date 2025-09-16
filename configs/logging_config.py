import logging
import os
import sys

import structlog


def configure_logging():
    log_level = logging.DEBUG if os.getenv("LOG_LEVEL") == "DEBUG" else logging.INFO

    error_log_handler = logging.StreamHandler(sys.stderr)
    error_log_handler.setLevel(logging.ERROR)

    renderer_processor = (
        structlog.dev.ConsoleRenderer()
        if log_level == logging.DEBUG
        else structlog.processors.JSONRenderer()
    )

    logging.basicConfig(level=log_level, format="%(message)s", stream=sys.stdout)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            renderer_processor,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
