# %%
import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from scipy.ndimage import gaussian_filter1d

from database_def import create_engine_table

engine, tables = create_engine_table()
access_log = tables["access_log"]
db_url = str(engine.url).replace("///", "//")
df = pl.read_sql(f"SELECT * from {access_log.name}", db_url)
remap = {"time_iso8601": "time"}
df.columns = [remap.get(c, c) for c in df.columns]
# %%
first_day = df["time"].min()
days_since = (df["time"] - first_day).dt.days()
days_counts = days_since.value_counts().sort("time")
plt.plot(days_counts["time"], days_counts["counts"])
# .sort_index().plot()
# %%
weekday = df["time"].dt.weekday()
weekday_counts = weekday.value_counts().sort(by="time")
plt.plot(weekday_counts["time"], weekday_counts["counts"])
plt.xticks(np.arange(7), ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])

# %%


# %%
def compute_date_hour_count(df: pl.DataFrame, frequency="1h") -> pl.DataFrame:
    date_hour = df["time"].dt.truncate(frequency)
    date_hour_count = date_hour.value_counts().sort(by="time")
    min_date = date_hour_count["time"].min()
    max_date = date_hour_count["time"].max()
    date_range = pl.date_range(min_date, max_date, interval=frequency, time_unit="ns")
    date_range_df = pl.DataFrame({"time": date_range})
    date_hour_count.join(date_range_df, on="time", how="outer").fill_null(0)
    return date_hour_count


date_hour_count = compute_date_hour_count(df)


# %%
def make_pages_df(df, lazy=True):
    if lazy:
        df = df.lazy()
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
    if lazy:
        return df_pages.collect()
    else:
        return df_pages


pages_df = make_pages_df(df, lazy=True)
# %%
"""plenty of good ideas, but let's for now focus on things specific to each web page; 
We can make a couple simple plots, and benchmark how fast the data is to compute. 
"""
webpages_df = (
    pages_df["page_name"]
    .value_counts()
    .filter(pl.col("counts") > 10)
    .sort(by="page_name")
)
webpage_list = list(webpages_df["page_name"])
print(webpage_list)

page = "python-docx"

single_page_df = pages_df.filter(pl.col("page_name") == page)
# %%
"""Plot of most popular times of day"""


# single_page_df["time"].dt.hour()+single_page_df["time"].dt.hour()
def get_hour_minute_count(df: pl.DataFrame, time_res_minutes: int) -> pl.DataFrame:
    h_m = df.select(
        (
            (
                pl.col("time").dt.hour() * 3600
                + pl.col("time").dt.truncate(f"{time_res_minutes}m").dt.minute() * 60
            )
            * 1e9
        )
        .cast(pl.Time)
        .alias("hour_minute")
    )

    h_m_count = h_m["hour_minute"].value_counts().sort("hour_minute")
    all_times_series = pl.Series(
        np.arange(24 * 60 // time_res_minutes) * time_res_minutes * 60 * 1e9
    ).cast(pl.Time)
    all_times_df = pl.DataFrame({"hour_minute": all_times_series})
    return h_m_count.join(all_times_df, on="hour_minute", how="outer").fill_null(0)


hour_minute_count = get_hour_minute_count(single_page_df, 10)


plt.plot(
    hour_minute_count["hour_minute"].cast(float) / 1e9 / 3600,
    gaussian_filter1d(hour_minute_count["counts"].cast(pl.Float32), 3, mode="wrap"),
)
plt.xlim(0, 24)
plt.xticks(range(0, 25))
plt.show()

# %%
"""Plot trend line. Here we start with just day-level precision."""
import datetime as dt

page = "home"
single_page_df = pages_df.filter(pl.col("page_name") == page)


def get_rolling_mean_1w(df: pl.DataFrame, frequency: str = "6h") -> pl.DataFrame:
    hour_count_df = compute_date_hour_count(df, frequency=frequency)
    rolling_sum = hour_count_df.select(
        pl.col("time"),
        pl.col("counts").rolling_mean(window_size="1w", closed="none", by="time"),
    )
    return rolling_sum


rolling_sum = get_rolling_mean_1w(single_page_df, "6h")
plt.plot(
    rolling_sum["time"], gaussian_filter1d(rolling_sum["counts"].cast(pl.Float32), 4)
)
ax = plt.gca()
ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
plt.show()

# %%
"""
Next all the interesting information has to do with geolocation. Here we should find
a good API and find a good way to insert the geolocation data at an early stage,
but also avoiding redoing the work. The way I see it, we insert it in pages_df,
and we store page_df to disk. Ingesting new parts of the logs should then incrementally 
add stuff to pages_df. 

But let's do that tomorrow lol.
"""
# %%
page_names_per_connection = pages_df.groupby("connection")["page_name"].nunique()
page_names_per_connection.value_counts() / page_names_per_connection.size
# %%

# %%
df["status"].value_counts()
# %%
# referers = referers.str.extract(r"\/([^\/]+)\/?$")
pd.value_counts(referers).to_clipboard()

# %%
plt.figure(figsize=(10, 5))
plt.ylabel("Number of requests")
plt.xlabel("Date")
date_hour_count.to_csv("date_hour_count.csv")

# %%
"""Actually just using pure request count doesn't make much sense, since different
webpages have different number of requests. We should filter by requests for actual
webpages first, I suppose. 

I guess we can filter by http_referrer, and just take those that come from my own website.
"""

# %%
