"""Application logger. Writes to a local file so CLI output stays clean."""

import logging
from pathlib import Path

LOGGER_NAME = "foundry"


def get_logger():
    """Return the shared Foundry logger."""
    return logging.getLogger(LOGGER_NAME)


def setup_logging(log_path=None, level=logging.INFO):
    """Attach a file handler. Safe to call more than once."""
    logger = get_logger()
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_path is not None:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.debug("Logger ready at level %s", logging.getLevelName(level))
    return logger
