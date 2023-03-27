# %%
"""
Run parse_access_log.py
"""

from log_parsing.parse_access_log import _main
from log_parsing.config import DATA_PATH, LOGS_PATH, logger
from log_parsing.database_def import SQLITE_DB_PATH
from pathlib import Path

# first make a backup of access.db
BACKUP_PATH = DATA_PATH / "backups"
BACKUP_PATH.mkdir(exist_ok=True)
if SQLITE_DB_PATH.exists():
    SQLITE_DB_PATH.rename(BACKUP_PATH / SQLITE_DB_PATH.name)

# Move all the items out of /parsed
log_files = (LOGS_PATH / "parsed").glob("*")
for log_file in log_files:
    log_file.rename(LOGS_PATH / log_file.name)

# run the main function of parse_access_log
_main()
# %%
