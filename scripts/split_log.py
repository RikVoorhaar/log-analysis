# %%
"""
Split the log into multiple parts; this is to emulate a more realistic use case
"""

from pathlib import Path
import json
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from log_parsing.config import PROJECT_ROOT
import dateutil.parser

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

ACCES_LOG_FILE = PROJECT_ROOT / "access.log"

with open(ACCES_LOG_FILE, "r") as f:
    start_time = datetime(1980, 1, 1, tzinfo=ZoneInfo("UTC"))
    write_file = open(LOG_DIR / "week0.log", "w")
    weeknum = 0
    for i, line in enumerate(f):
        data = json.loads(line)
        time = dateutil.parser.isoparse(data["time_iso8601"])
        if time - start_time > timedelta(days=7):
            start_time = time
            write_file.close()
            write_file = open(LOG_DIR / f"week{weeknum}.log", "w")
            weeknum += 1

        write_file.write(line)
