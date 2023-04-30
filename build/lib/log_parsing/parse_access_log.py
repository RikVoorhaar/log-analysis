# %%
import json

import dateutil.parser
import polars as pl
from io import TextIOWrapper
from time import perf_counter

from log_parsing.database_def import TableNames, create_engine_table
from log_parsing.config import PROJECT_ROOT, logger
from log_parsing.geolocation import add_country_info


def parse_data(data: dict, columns) -> dict:
    data = {k: v for k, v in data.items() if k in columns}
    time = dateutil.parser.isoparse(data["time_iso8601"])
    data["time_iso8601"] = time
    return data


def ingest_access_log(log_file: TextIOWrapper):
    """
    Ingest the access log into the database.
    """
    engine, tables = create_engine_table()
    access_log = tables[TableNames.ACCESS_LOG]
    columns = frozenset(access_log.columns.keys())

    min_date = None
    max_date = None
    tot_num_entries = 0
    with engine.connect() as conn:
        batch_size = 1000
        data_list = []
        stmt = access_log.insert().prefix_with("OR IGNORE")
        for line in log_file:
            data = json.loads(line)
            data = parse_data(data, columns)

            time = data["time_iso8601"]
            if min_date is None or time < min_date:
                min_date = time
            if max_date is None or time > max_date:
                max_date = time
            data_list.append(data)
            if len(data_list) >= batch_size:
                conn.execute(stmt, data_list)
                tot_num_entries += len(data_list)
                data_list = []
        tot_num_entries += len(data_list)
        conn.execute(stmt, data_list)
        conn.commit()
    logger.info(
        f"Commited {tot_num_entries} from access log "
        f"with date range {min_date} to {max_date}"
    )
    return min_date, max_date


def make_pages_df(df: pl.DataFrame):
    """
    Parse the `access_log` table to create the `pages_log` table.
    """
    df_pages = df.filter(
        (pl.col("request_uri").str.ends_with("/")) & (pl.col("status") == 200)
    )
    df_pages = df_pages.select(
        ["request_id", "request_uri", "addr", "time", "connection"]
    ).with_columns(
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
    df_pages = add_country_info(df_pages)
    df_pages = df_pages.drop("request_uri")
    return df_pages


# %%


def make_insert_pages(start_date, end_date):
    """
    Wrangle the data from the `access_log` table in between start_date and end_date
    and upsert in the `pages_log` table.
    """
    engine, tables = create_engine_table()
    access_log = tables[TableNames.ACCESS_LOG]
    pages_log = tables[TableNames.PAGES_LOG]
    db_url = str(engine.url).replace("///", "//")
    access_df = pl.read_sql(
        f"SELECT * from {access_log.name} "
        f"WHERE time_iso8601 >= '{start_date}' AND time_iso8601 <= '{end_date}';",
        db_url,
    )
    remap = {"time_iso8601": "time", "http_x_forwarded_for": "addr"}
    access_df.columns = [remap.get(c, c) for c in access_df.columns]

    pages_df = make_pages_df(access_df)
    logger.info(f"Made pages dataframe with shape {pages_df.shape}")
    with engine.connect() as conn:
        stmt = pages_log.insert().prefix_with("OR IGNORE").values(pages_df.rows())
        conn.execute(stmt)
        conn.commit()
    logger.info("Inserted pages dataframe into database.")


def load_df_from_db(
    df_name: TableNames, remap_iso8601: bool = True, extr_sql_stmt: str | None = None
):
    engine, tables = create_engine_table()
    table = tables[df_name]
    db_url = str(engine.url).replace("///", "//")

    sql_stmt = f"SELECT * from {table.name}"
    if extr_sql_stmt is not None:
        sql_stmt += " " + extr_sql_stmt
    df = pl.read_sql(sql_stmt, db_url)

    if remap_iso8601:
        remap = {"time_iso8601": "time"}
        df.columns = [remap.get(c, c) for c in df.columns]
    return df


def parse_ingest_file(file: TextIOWrapper):
    time_before = perf_counter()
    logger.info("Ingesting access log into database")
    start_date, end_date = ingest_access_log(file)
    time_taken_ms = (perf_counter() - time_before) * 1000
    logger.info(f"Ingest took {time_taken_ms:.2f} ms")

    time_before = perf_counter()
    logger.info(f"(Re)parsing access table from {start_date} to {end_date}")
    make_insert_pages(start_date, end_date)
    time_taken_ms = (perf_counter() - time_before) * 1000
    logger.info(f"Reparse took {time_taken_ms:.2f} ms")


def _main():
    LOG_PATH = PROJECT_ROOT / "logs"
    LOG_PARSED = LOG_PATH / "parsed"
    LOG_PARSED.mkdir(exist_ok=True)
    log_files = list(LOG_PATH.glob("*.log"))
    log_files.sort()
    logger.info(f"Parsing {len(log_files)} log files.")
    for log_file in log_files:
        logger.info(f"Parsing log file with name {log_file}")
        with open(log_file, "r") as log_file_stream:
            start_date, end_date = ingest_access_log(log_file_stream)
        log_file.rename(LOG_PARSED / log_file.name)
        make_insert_pages(start_date, end_date)


if __name__ == "__main__":
    _main()
