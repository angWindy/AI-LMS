"""Central logging setup for backend services."""
import logging


DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logging once for the backend process."""
    normalized_level = (log_level or "INFO").upper()
    if normalized_level not in VALID_LOG_LEVELS:
        normalized_level = "INFO"

    resolved_level = getattr(logging, normalized_level, logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=resolved_level,
            format=DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_DATE_FORMAT,
        )
    else:
        root_logger.setLevel(resolved_level)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
        for handler in root_logger.handlers:
            handler.setLevel(resolved_level)
            if handler.formatter is None:
                handler.setFormatter(formatter)

    logging.getLogger(__name__).info(
        "[Success] Logging configured level=%s",
        normalized_level,
    )
