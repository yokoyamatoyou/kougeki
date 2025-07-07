import logging
from logging.handlers import RotatingFileHandler

from .config import settings


def setup_logging() -> None:
    """Configure root logger with rotating file and console handlers."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    file_handler = RotatingFileHandler(
        settings.log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
