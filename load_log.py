# %%
import json
from pathlib import Path

import dateutil.parser
from tqdm import tqdm

from database_def import create_engine_table

log_file = Path("access.log")

ids = set()

with log_file.open("r") as f:
    lines = f.readlines()
    for i, line in enumerate(tqdm(lines)):
        data = json.loads(line)
        request_id = data["request_id"]
        if request_id in ids:
            print(f"Duplicate id {request_id} at line {i}")
            break
        ids.add(request_id)



engine, access_log = create_engine_table()

columns = frozenset(access_log.columns.keys())


def parse_data(data: dict) -> dict:
    data = {k: v for k, v in data.items() if k in columns}
    time = dateutil.parser.isoparse(data["time_iso8601"])
    data["time_iso8601"] = time
    return data


with engine.connect() as conn:
    with log_file.open("r") as f:
        batch_size = 1000
        data_list = []
        for i, line in enumerate(tqdm(f)):
            data = json.loads(line)
            data = parse_data(data)
            data_list.append(data)
            if len(data_list) >= batch_size:
                stmt = access_log.insert().prefix_with("OR IGNORE")
                conn.execute(stmt, data_list)
                data_list = []
    conn.commit()

# %%