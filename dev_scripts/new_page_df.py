# %%
import datetime
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from scipy.ndimage import gaussian_filter1d

from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db

df = load_df_from_db(TableNames.PAGES_LOG)
# df['timezone'].str.extract(r'(.*?)/.*').value_counts()
df["continent"].value_counts()
# %%


def filter_df(
    df: pl.DataFrame,
    date_start: datetime.datetime | None = None,
    date_end: datetime.datetime | None = None,
    country: str | None = None,
    continent: str | None = None,
    page_name: str | None = None,
) -> pl.DataFrame:
    selectors = []
    if date_start is not None and date_end is not None:
        selectors.append(pl.col("time").is_between(date_start, date_end))
    elif date_start is not None and date_end is None:
        selectors.append(pl.col("time") >= date_start)
    elif date_start is None and date_end is not None:
        selectors.append(pl.col("time") <= date_end)
    if country is not None:
        selectors.append(pl.col("country") == country)
    if continent is not None:
        selectors.append(pl.col("continent") == continent)
    if page_name is not None:
        selectors.append(pl.col("page_name") == page_name)
    if len(selectors) == 0:
        return df

    filter_predicate = selectors[0]
    for expr in selectors[1:]:
        filter_predicate &= expr
    return df.filter(filter_predicate)


date_start = df["time"][0]
date_end = df["time"][-1]
df_filtered = filter_df(df, date_start, date_end, continent="Europe", page_name="home")


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


def get_hour_minute_count(
    df: pl.DataFrame, time_res_minutes: int, column="time"
) -> pl.DataFrame:
    h_m = df.select(
        (
            (
                pl.col(column).dt.hour() * 3600
                + pl.col(column).dt.truncate(f"{time_res_minutes}m").dt.minute() * 60
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


class FilterMode(Enum):
    WRAP = "wrap"
    REFLECT = "reflect"
    MIRROR = "MIRROR"


def make_filter_map(sigma: float, mode: FilterMode = FilterMode.REFLECT):
    def gaussian_filter_map(x: pl.Series):
        return pl.Series(gaussian_filter1d(x.cast(pl.Float32), sigma, mode=mode.value))

    return gaussian_filter_map


def make_hour_minute_plot(df):
    hour_minute = get_hour_minute_count(df, 10, "local_time")
    hour_minute = hour_minute.with_columns(
        pl.col("hour_minute").cast(float) / 1e9 / 3600,
        pl.col("counts").map(make_filter_map(5, FilterMode.WRAP)) / pl.col("counts").sum(),
    )
    return px.line(hour_minute.to_pandas(), x="hour_minute", y="counts")



fig1 = make_hour_minute_plot(df)
fig2 = make_hour_minute_plot(df_filtered)
fig3 = go.Figure(data=fig1.data + fig2.data)
fig3
# %%


# %%
def get_rolling_mean_1w(df: pl.DataFrame, frequency: str = "6h") -> pl.DataFrame:
    hour_count_df = compute_date_hour_count(df, frequency=frequency)
    rolling_sum = hour_count_df.select(
        pl.col("time"),
        pl.col("counts").rolling_mean(window_size="1w", closed="none", by="time"),
    )
    return rolling_sum


rolling_sum = get_rolling_mean_1w(df, "6h")
plt.plot(
    rolling_sum["time"], gaussian_filter1d(rolling_sum["counts"].cast(pl.Float32), 4)
)
ax = plt.gca()
ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
plt.show()

# %%

weekday_df = df["weekday"].value_counts().sort(by="weekday")
days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
fig = px.bar(x=days_of_week, y=weekday_df["counts"], labels={"x": "", "y": "fraction"})

fig
