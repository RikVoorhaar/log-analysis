# %%
import datetime
from enum import Enum
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
import pandas as pd
from scipy.ndimage import gaussian_filter1d

from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db

df = load_df_from_db(TableNames.PAGES_LOG)
# df['timezone'].str.extract(r'(.*?)/.*').value_counts()
df["continent"].value_counts()
# %%


class FilteredDataFrame:
    def __init__(
        self,
        df: pl.DataFrame,
        date_start: datetime.datetime | None = None,
        date_end: datetime.datetime | None = None,
        country: str | None = None,
        continent: str | None = None,
        page_name: str | None = None,
    ):
        self.date_start = date_start
        self.date_end = date_end
        self.country = country
        self.continent = continent
        self.page_name = page_name

        self.dataframe = self._filter_df(df)

    def _get_filter_predicate(self) -> pl.Expr | None:
        selectors = []
        if self.date_start is not None and self.date_end is not None:
            selectors.append(pl.col("time").is_between(self.date_start, self.date_end))
        elif self.date_start is not None and self.date_end is None:
            selectors.append(pl.col("time") >= self.date_start)
        elif date_start is None and date_end is not None:
            selectors.append(pl.col("time") <= self.date_end)
        if self.country is not None:
            selectors.append(pl.col("country") == self.country)
        if self.continent is not None:
            selectors.append(pl.col("continent") == self.continent)
        if self.page_name is not None:
            selectors.append(pl.col("page_name") == self.page_name)
        if len(selectors) == 0:
            return None

        filter_predicate = selectors[0]
        for expr in selectors[1:]:
            filter_predicate &= expr
        return filter_predicate

    def _label_list(self) -> list[str]:
        """Return filter labels not related to the date range"""
        labels = []
        if self.country is not None:
            labels.append(f"Country={self.country}")
        if self.continent is not None:
            labels.append(f"Continent={self.continent}")
        if self.page_name is not None:
            labels.append(f"Page={self.page_name}")
        return labels

    @property
    def plot_label(self) -> str:
        label_list = self._label_list()
        if len(label_list) == 0:
            return "All"
        else:
            return " | ".join(label_list)

    def _filter_df(
        self,
        df: pl.DataFrame,
    ) -> pl.DataFrame:
        filter_predicate = self._get_filter_predicate()
        if filter_predicate is None:
            return df
        return df.filter(filter_predicate)

    def __repr__(self) -> str:
        repr_str = "Filter("
        property_stings = [f"<pl.DataFrame of shape{self.dataframe.shape}>"]
        for property in ["date_start", "date_end", "country", "continent", "page_name"]:
            if getattr(self, property) is not None:
                property_stings.append(f"{property}={getattr(self, property)}")
        repr_str += ", ".join(property_stings) + ")"
        return repr_str


date_start = df["time"][0]
date_end = df["time"][-1]
filtered_dfs = [
    FilteredDataFrame(df),
    FilteredDataFrame(df, continent="Europe"),
    FilteredDataFrame(df, country="Denmark"),
    FilteredDataFrame(df, page_name="home"),
]
filtered_dfs


# %%
def compute_date_hour_count(df: pl.DataFrame, frequency="1h") -> pl.DataFrame:
    date_hour = df["time"].dt.truncate(frequency)
    date_hour_count = date_hour.value_counts().sort(by="time")
    min_date = date_hour_count["time"].min()
    max_date = date_hour_count["time"].max()
    date_range = pl.date_range(min_date, max_date, interval=frequency, time_unit="ns")
    date_range_df = pl.DataFrame({"time": date_range})
    date_hour_count = date_hour_count.join(
        date_range_df, on="time", how="outer"
    ).fill_null(0)
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


class GaussianFilterMode(Enum):
    WRAP = "wrap"
    REFLECT = "reflect"
    MIRROR = "MIRROR"


def make_filter_map(
    sigma: float, mode: GaussianFilterMode = GaussianFilterMode.REFLECT
):
    def gaussian_filter_map(x: pl.Series):
        return pl.Series(gaussian_filter1d(x.cast(pl.Float32), sigma, mode=mode.value))

    return gaussian_filter_map


def make_hour_minute_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    x_label = "Time of day"
    y_label = "relative frequency"
    hour_minute = get_hour_minute_count(df, 10, "local_time")
    hour_minute = hour_minute.with_columns(
        pl.col("hour_minute").dt.strftime("%H:%M").alias(x_label),
        (
            pl.col("counts").map(make_filter_map(5, GaussianFilterMode.WRAP))
            / pl.col("counts").sum()
        ).alias(y_label),
    )
    return hour_minute


def make_line_plot(
    filter_dfs: list[FilteredDataFrame],
    plot_data_function: Callable[[pl.DataFrame], pl.DataFrame],
    x_label: str,
    y_label: str,
    x_axis_kwargs: dict | None = None,
    y_axis_kwargs: dict | None = None,
    layout_kwargs: dict | None = None,
) -> go.Figure:
    plot_dfs = [plot_data_function(df.dataframe) for df in filter_dfs]
    fig = go.Figure()
    for filter, plot_df in zip(filter_dfs, plot_dfs):
        fig.add_trace(
            go.Scatter(
                x=plot_df[x_label],
                y=plot_df[y_label],
                name=filter.plot_label,
                hovertemplate=r"%{y:.4f}<extra></extra>",
            )
        )

    fig.update_traces(mode="lines")
    if layout_kwargs is None:
        layout_kwargs = {}
    fig.update_layout(
        legend_title_text="Filter", hovermode="x unified", **layout_kwargs
    )
    if x_axis_kwargs is None:
        x_axis_kwargs = {}
    fig.update_xaxes(title_text=x_label, **x_axis_kwargs)  # , tickformat="%H:%M")
    if y_axis_kwargs is None:
        y_axis_kwargs = {}
    fig.update_yaxes(title_text=y_label, **y_axis_kwargs)
    return fig


make_line_plot(
    filtered_dfs,
    make_hour_minute_plot_data,
    "Time of day",
    "relative frequency",
    x_axis_kwargs={"tickformat": "%H:%M"},
)


# %%
def get_rolling_mean_1w(df: pl.DataFrame) -> pl.DataFrame:
    x_label = "date"
    y_label = "relative_counts"
    hour_count_df = compute_date_hour_count(df, frequency="6h")
    rolling_sum = hour_count_df.select(
        pl.col("time").alias(x_label),  # .dt.strftime(r"%Y/%m/%d"),
        pl.col("counts")
        .rolling_mean(window_size="1w", closed="none", by="time")
        .map(make_filter_map(5, GaussianFilterMode.REFLECT))
        .alias(y_label)
        / len(df),
    )
    return rolling_sum


make_line_plot(
    filtered_dfs,
    get_rolling_mean_1w,
    "date",
    "relative_counts",
)
# %%


def make_weekday_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    weekday_df = df["weekday"].value_counts().sort(by="weekday")
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekday_df = weekday_df.with_columns(
        pl.Series(days_of_week).alias("weekday"),
        (pl.col("counts") / pl.col("counts").sum()).alias("Fraction"),
    )
    return weekday_df


def make_weekday_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    weekday_dfs = [make_weekday_plot_data(df.dataframe) for df in filtered_dfs]
    x_label = "weekday"
    y_label = "Fraction"
    fig = go.Figure()
    for filter, wk_df in zip(filtered_dfs, weekday_dfs):
        fig.add_trace(
            go.Bar(
                x=wk_df[x_label],
                y=wk_df[y_label],
                name=filter.plot_label,
                hovertemplate=r"%{y:.4f}<extra></extra>",
            )
        )
    fig.update_layout(legend_title_text="Filter")
    return fig


make_weekday_plot(filtered_dfs)
# %%

df = filtered_dfs[0].dataframe

IGNORED_PAGES = ["test", "users", "images"]
ignore_pages_regex = r"^(" + "|".join(IGNORED_PAGES) + ")$"


def make_page_popularity_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    df_bar = (
        df["page_name"]
        .value_counts()
        .sort(by="page_name")
        .filter(pl.col("page_name").str.contains(ignore_pages_regex).is_not())
        .with_columns((pl.col("counts") / pl.col("counts").sum()))
    )
    x_label = "Page name"
    y_label = "Frequency"
    df_bar.columns = [x_label, y_label]
    return df_bar


def make_page_popularity_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    height_per_row = 60
    x_label = "Page name"
    y_label = "Frequency"
    fig = go.Figure()
    all_labels: set[str] = set()
    for filter in filtered_dfs:
        df_bar = make_page_popularity_plot_data(filter.dataframe)
        all_labels.update(df_bar[x_label])
        fig.add_trace(
            go.Bar(
                y=df_bar[x_label],
                x=df_bar[y_label],
                orientation="h",
                name=filter.plot_label,
                hovertemplate=r"%{x:.4f}<extra></extra>",
            )
        )

    fig.update_xaxes(type="log", automargin=True)
    fig.update_yaxes(automargin=True)
    fig.update_layout(
        height=len(all_labels) * height_per_row, legend_title_text="Filter"
    )
    return fig


make_page_popularity_plot(filtered_dfs)

# %%
"""
Now let's think about country data. Continents are obviously easy, but countries are
tougher. I map would of course be cool, but how to represent that data?

Let's see first if we can make a country map.

For this we are going to need three leter iso codes as feature. Unfortunately we only
have 2-letter iso. Let's if that also works or if we need to translate 2 letter to 3
letter.
"""
import country_converter as coco

plot_df = (
    df["country_iso"]
    .value_counts()
    .with_columns(pl.col("counts").cast(pl.Float32))
    .to_pandas()
)
cc = coco.CountryConverter()

plot_df["country_iso"] = cc.pandas_convert(series=plot_df["country_iso"], to="ISO3")
px.choropleth(plot_df, locations="country_iso", color="counts")

# %%
"""
So this is not that interesting. We have to compare it to the 'all' category, or to 
population or something. Or use 'all' to build a bayesian model for how much we should expect...

I think here it may just make sense to strictly allow the comparison of two filters only. 
So for that we need extra functionality. Let's shelf it for now, and isntead 
compare continents.

What we _could_ do is list the top 10 most popular countries for example. We can then 
build in a slider for the user to select the number of countries in the plot. 

How do we decide the top 10? We can put everything into one big dataframe and then 
sort by the max of the rows and just take the top N; that's relatively intuitive and 
simple to implement
"""
# %%

def make_country_plot(filtered_df: list[FilteredDataFrame]) -> go.Figure:
    plot_labels = [fdf.plot_label for fdf in filtered_dfs]
    x_label = "Country"
    val_counts = [
        fdf.dataframe["country"]
        .alias(x_label)
        .value_counts()
        .sort(by=x_label)
        .with_columns(pl.col("counts").cast(pl.Float32) / pl.col("counts").sum())
        .rename({"counts": fdf.plot_label})
        for fdf in filtered_dfs
    ]
    joined = val_counts[0]
    for val_df in val_counts[1:]:
        joined = joined.join(val_df, on=x_label, how="outer")
    counts_columns = [col for col in joined.columns if col != x_label]
    joined = (
        joined.fill_null(0)
        .with_columns(pl.max(counts_columns).alias("_counts_max"))
        .sort(by="_counts_max", descending=True)
    ).drop("_counts_max")
    top10 = joined[:10]
    top10

    fig = px.bar(
        top10.to_pandas(), y="Country", x=plot_labels, barmode="group", orientation="h"
    )
    height_per_row = 60
    fig.update_layout(height=len(top10) * height_per_row, legend_title_text="Filter")
    return fig

make_country_plot(filtered_dfs)


# %%
def make_continent_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    plot_df = df["continent"].value_counts().sort(by="continent")
    plot_df = plot_df.with_columns(
        (pl.col("counts") / pl.col("counts").sum()).alias("Fraction"),
    )
    return plot_df


def make_continent_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    plot_df_list = [make_continent_plot_data(df.dataframe) for df in filtered_dfs]
    x_label = "continent"
    y_label = "Fraction"
    fig = go.Figure()
    for filter, wk_df in zip(filtered_dfs, plot_df_list):
        fig.add_trace(
            go.Bar(
                x=wk_df[y_label],
                y=wk_df[x_label],
                name=filter.plot_label,
                hovertemplate=r"%{x:.4f}<extra></extra>",
                orientation="h",
            )
        )
    fig.update_layout(legend_title_text="Filter")
    return fig


make_continent_plot(filtered_dfs)
