import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent
LOGGER_NAME = "parser_logger"


def setup_logger():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    log_file = PROJECT_ROOT / "parser.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(module)s | %(levelname)s\n    %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()


def log_exception(*args):
    logger.exception("Exception occurred", exc_info=args)


sys.excepthook = log_exception
logger.info("Logger initialized")
