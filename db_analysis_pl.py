# %%
import matplotlib.pyplot as plt
from database_def import create_engine_table
import polars as pl
import numpy as np

engine, access_log = create_engine_table()
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
def compute_date_hour_count(df: pl.DataFrame) -> pl.DataFrame:
    date_hour = df["time"].dt.truncate("1h")
    date_hour_count = date_hour.value_counts().sort(by="time")
    min_date = date_hour_count["time"].min()
    max_date = date_hour_count["time"].max()
    date_range = pl.date_range(min_date, max_date, interval="1h", time_unit='ns')
    date_range_df = pl.DataFrame({"time": date_range})
    date_hour_count.join(date_range_df, on="time", how="outer").fill_null(0)
    return date_hour_count


%time date_hour_count = compute_date_hour_count(df)
# %%
weekday_counts.set_index("date_hour")


# %%
def make_pages_df(df, lazy=True):
    if lazy:
        df = df.lazy()
    df_pages = df.filter(
    (pl.col("request_uri").str.ends_with("/")) & (pl.col("status") == 200)
    )
    df_pages = df_pages.select(["request_uri","time","connection"]).with_columns([
        (pl.col("time").dt.truncate("1h")).alias("hour"),
        (pl.col("time").dt.truncate("1d")).alias("day"),
        (pl.col("time").dt.weekday().alias("weekday")),
        (pl.col("request_uri").str.extract(r"/([^/]+)/?$").fill_null("home").alias("page_name"))
    ])
    df_pages = df_pages.drop("request_uri")
    if lazy:
        return df_pages.collect()
    else:
        return df_pages

df_pages = make_pages_df(df, lazy=True)
#%%
df.filter([
    pl.col("connection") < 100
]
)
#%%
df_pages["hour"] = df_pages["time"].dt.truncate("1h")
df_pages["day"] = df_pages["hour"].dt.truncate("1d")
df_pages["weekday"] = df_pages["day"].dt.weekday()
df_pages["page_name"] = referers
# %%
def make_pages_df(df):
    mask = (df["request_uri"].str.endswith("/")) & (df["status"] == 200)
    df_pages = df[mask]
    referers = df_pages["request_uri"].str.extract(r"\/([^\/]+)\/?$").fillna("home")
    df_pages = df_pages[["time", "connection"]]
    df_pages["hour"] = df_pages["time"].dt.floor("H")
    df_pages["day"] = df_pages["hour"].dt.floor("D")
    df_pages["weekday"] = df_pages["day"].dt.weekday
    df_pages["page_name"] = referers
    return df_pages


pages_df = make_pages_df(df)
# %%
"""plenty of good ideas, but let's for now focus on things specific to each web page; 
We can make a couple simple plots, and benchmark how fast the data is to compute. 
"""
webpages = pages_df["page_name"].value_counts()
webpages = webpages[webpages > 10]
webpages

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
