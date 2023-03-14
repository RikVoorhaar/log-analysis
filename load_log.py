# %%
import json
from pathlib import Path

import dateutil.parser
import polars as pl
from tqdm import tqdm

from database_def import create_engine_table


def parse_data(data: dict, columns) -> dict:
    data = {k: v for k, v in data.items() if k in columns}
    time = dateutil.parser.isoparse(data["time_iso8601"])
    data["time_iso8601"] = time
    return data


def ingest_log(log_file: Path):
    engine, access_log = create_engine_table()
    columns = frozenset(access_log.columns.keys())

    min_date = None
    max_date = None
    with engine.connect() as conn:
        with log_file.open("r") as f:
            batch_size = 1000
            data_list = []
            for i, line in enumerate(tqdm(f)):
                data = json.loads(line)
                data = parse_data(data, columns)

                time = data["time_iso8601"]
                if min_date is None or time < min_date:
                    min_date = time
                if max_date is None or time > max_date:
                    max_date = time
                data_list.append(data)
                if len(data_list) >= batch_size:
                    stmt = access_log.insert().prefix_with("OR IGNORE")
                    conn.execute(stmt, data_list)
                    data_list = []
        conn.commit()
    return min_date, max_date


def make_pages_df(df: pl.DataFrame):
    df_pages = df.filter(
        (pl.col("request_uri").str.ends_with("/")) & (pl.col("status") == 200)
    )
    df_pages = df_pages.select(["request_uri", "time", "connection"]).with_columns(
        [
            (pl.col("time").dt.truncate("1h")).alias("hour"),
            (pl.col("time").dt.truncate("1d")).alias("day"),
            (pl.col("time").dt.weekday().alias("weekday")),
            (
                pl.col("request_uri")
                .str.extract(r"/([^/]+)/?$")
                .fill_null("home")
                .alias("page_name")
            ),
        ]
    )
    df_pages = df_pages.drop("request_uri")
    return df_pages


def load_access_db_pl() -> pl.DataFrame:
    engine, access_log = create_engine_table()
    db_url = str(engine.url).replace("///", "//")
    df = pl.read_sql(f"SELECT * from {access_log.name}", db_url)
    remap = {"time_iso8601": "time"}
    df.columns = [remap.get(c, c) for c in df.columns]
    return df


# %%

log_file = Path("logs/week0.log")
start_date, end_date = ingest_log(log_file)

print(start_date, end_date)
# %%

engine, access_log = create_engine_table()
db_url = str(engine.url).replace("///", "//")
df = pl.read_sql(
    f"SELECT * from {access_log.name} "
    f"WHERE time_iso8601 >= '{start_date}' AND time_iso8601 <= '{end_date}';",
    db_url,
)
remap = {"time_iso8601": "time"}
df.columns = [remap.get(c, c) for c in df.columns]
pages_df = make_pages_df(df)
pages_df