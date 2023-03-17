# %%
from pathlib import Path
from enum import Enum
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    Engine,
)


class TableNames(Enum):
    ACCESS_LOG = "access_log"
    PAGES_LOG = "pages_log"


SQLITE_DB_PATH = Path("data") / "access.db"


def create_engine_table() -> tuple[Engine, dict[TableNames, Table]]:
    engine = create_engine("sqlite:///" + str(SQLITE_DB_PATH))

    metadata = MetaData()
    access_log = Table(
        TableNames.ACCESS_LOG.value,
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

    pages_log = Table(
        TableNames.PAGES_LOG.value,
        metadata,
        Column("request_id", String, primary_key=True),
        Column("http_x_forwarded_for", String),
        Column("time", DateTime),
        Column("connection", Integer),
        Column("hour", DateTime),
        Column("day", DateTime),
        Column("weekday", Integer),
        Column("page_name", String),
    )

    metadata.create_all(engine, checkfirst=True)
    tables = {
        TableNames.ACCESS_LOG: access_log,
        TableNames.PAGES_LOG: pages_log,
    }
    return engine, tables
