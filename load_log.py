# %%
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import json

from pathlib import Path

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



# %%
data
# %%
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    DateTime,
    Float,
)
import dateutil.parser

engine = create_engine("sqlite:///access.db")

metadata = MetaData()
access_log = Table(
    "access_log",
    metadata,
    Column("request_id", String, primary_key=True),
    Column("connection", Integer),
    Column("connection_requests", Integer),
    Column("http_referer", String),
    Column("http_x_forwarded_for", String),
    Column("remote_addr", String),
    Column("request_method", String),
    Column("request_uri", String),
    Column("request_time", Float),
    Column("body_bytes_sent", Integer),
    Column("status", Integer),
    Column("time_iso8601", DateTime),
)

metadata.create_all(engine, checkfirst=True)

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

import pandas as pd

with engine.connect() as conn:
    stmt = access_log.select()
    df = pd.read_sql(stmt, conn)

# %%
first_day = df['time_iso8601'].dt.date.min()
days_since = df['time_iso8601'].dt.date - first_day
days_since.value_counts().sort_index().plot()
# %%
weekday = df['time_iso8601'].dt.weekday
weekday.value_counts().sort_index().plot()
plt.xticks(np.arange(7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])

# %%
df['connection'].value_counts().value_counts().sort_index().plot().set_yscale('log')
plt.ylabel('Number of requests')
plt.xlabel('Number of connections')
plt.show()

# %%
plt.figure(figsize=(10, 5))
date_hour = df['time_iso8601'].dt.floor('H')
date_hour_count = date_hour.value_counts().sort_index()
min_date = date_hour_count.index.min()
max_date = date_hour_count.index.max()
date_hour_count = date_hour_count.reindex(pd.date_range(min_date, max_date, freq='H')).fillna(0)
date_hour_count.rolling(24).sum().plot()
plt.ylabel('Number of requests')
plt.xlabel('Date')
date_hour_count.to_csv('date_hour_count.csv')

# %%