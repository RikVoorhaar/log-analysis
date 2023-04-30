# %%
import datetime
from enum import Enum
from typing import Callable

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import polars as pl
from pydantic import BaseModel, parse_obj_as, validator
from scipy.ndimage import gaussian_filter1d

from log_parsing.database_def import TableNames
from log_parsing.config import logger
from log_parsing.parse_access_log import load_df_from_db

IGNORED_PAGES = ["test", "users", "images"]
IGNORE_PAGES_REGEX = r"^(" + "|".join(IGNORED_PAGES) + ")$"
MARGINS = dict(margin_top=35, margin_bottom=20, margin_l=30, margin_r=0)
GO_MARGIN = go.layout.Margin(
    t=MARGINS["margin_top"],
    b=MARGINS["margin_bottom"],
    l=MARGINS["margin_l"],
    r=MARGINS["margin_r"],
)


class FilterModel(BaseModel):
    dateRange: tuple[datetime.datetime | None, datetime.datetime | None]
    countries: list[str] | None
    continents: list[str] | None
    pageNames: list[str] | None
    index: int

    @validator("dateRange", pre=True)
    def validate_date_range(cls, v):
        start, end = v
        date_format = r"%Y-%m-%d"
        if start == "":
            start_datetime = None
        else:
            start_datetime = datetime.datetime.strptime(start, date_format)

        if end == "":
            end_datetime = None
        else:
            end_datetime = datetime.datetime.strptime(end, date_format)
        return start_datetime, end_datetime

    @validator("countries", "continents", "pageNames", pre=True)
    def none_if_empty(cls, v):
        if len(v) == 0:
            return None
        return v

    @validator("index", pre=True)
    def unpack_list(cls, v):
        """Index is packet as list[str], but we just want a single int"""
        return int(v[0])

    def to_filtered_data_frame(self, df: pl.DataFrame, colors: list[str] | None = None):
        if colors is None:
            colors = px.colors.qualitative.T10
        color = colors[self.index % len(colors)]
        return FilteredDataFrame(
            df,
            date_start=self.dateRange[0],
            date_end=self.dateRange[1],
            countries=self.countries,
            continents=self.continents,
            page_names=self.pageNames,
            index=self.index,
            plot_color=color,
        )


class FilteredDataFrame:
    def __init__(
        self,
        df: pl.DataFrame,
        date_start: datetime.datetime | None = None,
        date_end: datetime.datetime | None = None,
        countries: list[str] | None = None,
        continents: list[str] | None = None,
        page_names: list[str] | None = None,
        index: int | None = None,
        plot_color: str | None = None,
    ):
        if index is None:
            index = 0
        self.index = index
        self.date_start = date_start
        self.date_end = date_end
        self.countries = countries
        self.continents = continents
        self.page_names = page_names
        self.plot_color = plot_color

        self.dataframe = self._filter_df(df)

    def _get_filter_predicate(self) -> pl.Expr | None:
        selectors = []
        if self.date_start is not None and self.date_end is not None:
            selectors.append(pl.col("time").is_between(self.date_start, self.date_end))
        elif self.date_start is not None and self.date_end is None:
            selectors.append(pl.col("time") >= self.date_start)
        elif self.date_start is None and self.date_end is not None:
            selectors.append(pl.col("time") <= self.date_end)

        if self.countries is not None:
            countries_regex = "|".join(self.countries)
            selectors.append(pl.col("country").str.contains(countries_regex))
        if self.continents is not None:
            continents_regex = "|".join(self.continents)
            selectors.append(pl.col("continent").str.contains(continents_regex))
        if self.page_names is not None:
            page_names_regex = "|".join(self.page_names)
            selectors.append(pl.col("page_name").str.contains(page_names_regex))
        if len(selectors) == 0:
            return None

        filter_predicate = selectors[0]
        for expr in selectors[1:]:
            filter_predicate &= expr
        return filter_predicate

    def _label_list(self) -> list[str]:
        """Return filter labels not related to the date range"""
        labels = []
        if self.countries is not None and len(self.countries) > 0:
            if len(self.countries) == 1:
                labels.append(f"Country={self.countries[0]}")
            else:
                countries_string = ", ".join(self.countries)
                labels.append(f"Countries=[{countries_string}]")
        if self.continents is not None:
            if len(self.continents) == 1:
                labels.append(f"Continent={self.continents[0]}")
            else:
                continents_string = ", ".join(self.continents)
                labels.append(f"Continents=[{continents_string}]")
        if self.page_names is not None:
            if len(self.page_names) == 1:
                labels.append(f"Page={self.page_names[0]}")
            else:
                page_names_string = ", ".join(self.page_names)
                labels.append(f"Pages=[{page_names_string}]")
        return labels

    @property
    def plot_number(self) -> str:
        return str(self.index + 1)

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
        for property in [
            "date_start",
            "date_end",
            "countries",
            "continents",
            "page_names",
        ]:
            if getattr(self, property) is not None:
                property_stings.append(f"{property}={getattr(self, property)}")
        repr_str += ", ".join(property_stings) + ")"
        return repr_str


def compute_date_hour_count(df: pl.DataFrame, frequency="1h") -> pl.DataFrame:
    date_hour = df["time"].dt.truncate(frequency)
    date_hour_count = date_hour.value_counts().sort(by="time")
    min_date = date_hour_count["time"].min()
    max_date = date_hour_count["time"].max()
    date_range = pl.date_range(
        min_date, max_date, interval=frequency, time_unit="ns"
    )  # type: ignore
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
    MIRROR = "mirror"


def make_filter_map(
    sigma: float, mode: GaussianFilterMode = GaussianFilterMode.REFLECT
):
    def gaussian_filter_map(x: pl.Series):
        return pl.Series(
            gaussian_filter1d(x.cast(pl.Float32).to_numpy(), sigma, mode=mode.value)
        )

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
    title: str | None = None,
) -> go.Figure:
    plot_dfs = [plot_data_function(df.dataframe) for df in filter_dfs]
    fig = go.Figure()
    for filter, plot_df in zip(filter_dfs, plot_dfs):
        fig.add_trace(
            go.Scatter(
                x=plot_df[x_label],
                y=plot_df[y_label],
                name=filter.plot_number,
                hovertemplate=r"%{y:.4f}<extra></extra>",
                line=dict(color=filter.plot_color),
            )
        )

    fig.update_traces(mode="lines")
    if layout_kwargs is None:
        layout_kwargs = {}
    fig.update_layout(
        title=title,
        legend_title_text="Filter",
        hovermode="x unified",
        legend=dict(x=0, y=1.1, orientation="h", xanchor="left"),
        height=450,
        **layout_kwargs,
    )
    if x_axis_kwargs is None:
        x_axis_kwargs = {}
    fig.update_xaxes(title_text=x_label, **x_axis_kwargs)  # , tickformat="%H:%M")
    if y_axis_kwargs is None:
        y_axis_kwargs = {}
    fig.update_yaxes(**y_axis_kwargs)
    return fig


def get_rolling_mean_1w(df: pl.DataFrame) -> pl.DataFrame:
    x_label = "date"
    y_label = "relative_counts"
    hour_count_df = compute_date_hour_count(df, frequency="1h")
    rolling_sum = hour_count_df.select(
        pl.col("time").alias(x_label),  # .dt.strftime(r"%Y/%m/%d"),
        pl.col("counts")
        .rolling_mean(window_size="1w", closed="none", by="time")
        .fill_null(0)
        .map(make_filter_map(20, GaussianFilterMode.WRAP))
        .alias(y_label)
        / len(df),
    )
    return rolling_sum


def make_weekday_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    weekday_df = df["weekday"].value_counts().sort(by="weekday")

    if len(weekday_df) < 7:
        weekday_all = pl.DataFrame({"weekday": np.arange(7) + 1})
        weekday_df = weekday_all.join(weekday_df, on="weekday", how="left").fill_null(0)

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
                name=filter.plot_number,
                hovertemplate=r"%{y:.4f}<extra></extra>",
                marker=dict(color=filter.plot_color),
            )
        )
    fig.update_layout(
        legend_title_text="Filter",
        legend=dict(x=0, y=1.1, orientation="h", xanchor="left"),
    )
    return fig


def make_page_popularity_plot_data(df: pl.DataFrame) -> pl.DataFrame:
    df_bar = (
        df["page_name"]
        .value_counts()
        .sort(by="page_name")
        .filter(pl.col("page_name").str.contains(IGNORE_PAGES_REGEX).is_not())
        .with_columns((pl.col("counts") / pl.col("counts").sum()))
    )
    x_label = "Page name"
    y_label = "Frequency"
    df_bar.columns = [x_label, y_label]
    return df_bar


def make_page_popularity_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
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
                name=filter.plot_number,
                hovertemplate=r"%{x:.4f}<extra></extra>",
                marker=dict(color=filter.plot_color),
            )
        )
    height_per_row = 20 + 5 * len(filtered_dfs)

    fig.update_xaxes(type="log", automargin=True)
    fig.update_yaxes(automargin=True)
    num_rows = len(all_labels)
    num_filters = len(filtered_dfs)
    height_per_row = 20 + 5 * num_filters
    inner_height = num_rows * height_per_row
    margin_top = MARGINS["margin_top"]
    margin_bottom = MARGINS["margin_bottom"]
    height = inner_height + margin_top + margin_bottom
    legend_y = 1 + margin_top / height
    fig.update_layout(
        height=height,
        legend_title_text="Filter",
        legend=dict(x=0, y=legend_y, orientation="h", xanchor="left"),
    )
    return fig


def make_country_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    plot_labels = [fdf.plot_number for fdf in filtered_dfs]
    x_label = "Country"
    val_counts = [
        fdf.dataframe["country"]
        .alias(x_label)
        .value_counts()
        .sort(by=x_label)
        .with_columns(pl.col("counts").cast(pl.Float32) / pl.col("counts").sum())
        .rename({"counts": fdf.plot_number})
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

    colors = [fdf.plot_color for fdf in filtered_dfs]
    fig = px.bar(
        top10.to_pandas(),
        y="Country",
        x=plot_labels,
        barmode="group",
        orientation="h",
        color_discrete_sequence=colors,
    )
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    num_filters = len(filtered_dfs)
    num_rows = len(top10)
    height_per_row = 20 + 5 * num_filters
    inner_height = num_rows * height_per_row
    margin_top = MARGINS["margin_top"]
    margin_bottom = MARGINS["margin_bottom"]
    height = inner_height + margin_top + margin_bottom
    legend_y = 1 + margin_top / height
    fig.update_layout(
        height=height,
        legend_title_text="Filter",
        legend=dict(x=0, y=legend_y, orientation="h", xanchor="left"),
    )
    return fig


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
    all_labels: set[str] = set()
    for filter, wk_df in zip(filtered_dfs, plot_df_list):
        all_labels.update(wk_df[x_label])
        fig.add_trace(
            go.Bar(
                x=wk_df[y_label],
                y=wk_df[x_label],
                name=filter.plot_number,
                hovertemplate=r"%{x:.4f}<extra></extra>",
                orientation="h",
                marker=dict(color=filter.plot_color),
            )
        )
    num_rows = len(all_labels)
    num_filters = len(filtered_dfs)
    height_per_row = 20 + 5 * num_filters
    inner_height = num_rows * height_per_row
    margin_top = MARGINS["margin_top"]
    margin_bottom = MARGINS["margin_bottom"]
    height = inner_height + margin_top + margin_bottom
    legend_y = 1 + margin_top / height
    fig.update_layout(
        height=height,
        legend_title_text="Filter",
        legend=dict(x=0, y=legend_y, orientation="h", xanchor="left"),
    )
    return fig


# %%

# %%


def make_time_of_day_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    return make_line_plot(
        filtered_dfs,
        make_hour_minute_plot_data,
        "Time of day",
        "relative frequency",
        x_axis_kwargs={"tickformat": "%H:%M"},
        # title="Time of day vs. relative frequency"
    )


def make_date_plot(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
    return make_line_plot(
        filtered_dfs,
        get_rolling_mean_1w,
        "date",
        "relative_counts",
        # title="Date vs. relative frequency",
    )


plot_functions: dict[str, Callable[[list[FilteredDataFrame]], go.Figure]] = {
    "Time of day": make_time_of_day_plot,
    "Date": make_date_plot,
    "Weekday": make_weekday_plot,
    "Continents": make_continent_plot,
    "Page popularity": make_page_popularity_plot,
    "Most active countries": make_country_plot,
}


def modify_layout(
    plot_func: Callable[[list[FilteredDataFrame]], go.Figure]
) -> Callable[[list[FilteredDataFrame]], go.Figure]:
    def new_plot_func(filtered_dfs: list[FilteredDataFrame]) -> go.Figure:
        fig = plot_func(filtered_dfs)
        fig.update_layout(margin=GO_MARGIN, autosize=False)
        return fig

    return new_plot_func


plot_functions = {name: modify_layout(func) for name, func in plot_functions.items()}


if __name__ == "__main__":
    df = load_df_from_db(TableNames.PAGES_LOG)
    date_start = df["time"][0]
    date_end = df["time"][-1]
    filtered_dfs = [
        FilteredDataFrame(df, index=0),
        FilteredDataFrame(df, continents=["Europe", "Asia"], index=1),
        FilteredDataFrame(df, countries=["Denmark", "Sweden"], index=2),
        FilteredDataFrame(df, page_names=["home"], index=3),
    ]

    for plot_function in plot_functions.values():
        plot_function(filtered_dfs).show()
