import logging
import os
import sys
from pathlib import Path

import dotenv

dotenv.load_dotenv()


def find_project_root(name: str = "log-analysis") -> Path:
    cwd = Path.cwd()
    while cwd.name != name:
        cwd = cwd.parent
        if cwd == Path("/"):
            raise FileNotFoundError(f"Could not find project root {name}")
    return cwd


try:
    PROJECT_ROOT = Path(os.environ["PROJECT_ROOT"])
except KeyError:
    PROJECT_ROOT = find_project_root()

DATA_PATH = PROJECT_ROOT / "data"
LOGS_PATH = PROJECT_ROOT / "logs"
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

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.ERROR)
    logger.addHandler(stdout_handler)

    return logger


logger = setup_logger()


def log_exception(*args):
    logger.exception("Exception occurred", exc_info=args)


sys.excepthook = log_exception
logger.info("Logger initialized")
