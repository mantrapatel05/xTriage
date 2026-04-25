import logging
import sys


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(level: str = "INFO") -> logging.Logger:
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(handler)

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(resolved_level)
    return logging.getLogger("bug_triage_agent")


logger = configure_logging()