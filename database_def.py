
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



def create_engine_table() -> tuple[Engine, Table]:
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
    return engine, access_log

# %%