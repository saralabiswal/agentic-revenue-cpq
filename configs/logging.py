import logging
import os


DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level: str | int | None = None) -> int:
    """Configure application logging once and return the resolved level."""

    resolved_level = _resolve_level(level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL))
    root_logger = logging.getLogger()
    root_logger.setLevel(resolved_level)

    configured_handler = _configured_handler(root_logger)
    if configured_handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handler.setLevel(resolved_level)
        handler._enterprise_platform_configured = True  # type: ignore[attr-defined]
        root_logger.addHandler(handler)
    else:
        configured_handler.setLevel(resolved_level)

    return resolved_level


def _resolve_level(level: str | int) -> int:
    if isinstance(level, int):
        return level

    normalized = level.upper()
    resolved = logging.getLevelName(normalized)
    if isinstance(resolved, int):
        return resolved

    return logging.INFO


def _configured_handler(logger: logging.Logger) -> logging.Handler | None:
    for handler in logger.handlers:
        if getattr(handler, "_enterprise_platform_configured", False):
            return handler
    return None
