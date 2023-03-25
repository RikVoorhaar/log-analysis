# %%
from pathlib import Path

import plotly.express as px
import polars as pl
from dash import Dash, Input, Output, dcc, html

from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db
from flask import request, jsonify
from log_parsing.plot_functions import FilteredDataFrame, make_weekday_plot

ASSETS = Path(__file__).parent / "assets"

df = load_df_from_db(TableNames.PAGES_LOG)
date_start = df["time"][0]
date_end = df["time"][-1]
filtered_dfs = [
    FilteredDataFrame(df),
    FilteredDataFrame(df, continent="Europe"),
    FilteredDataFrame(df, country="Denmark"),
    FilteredDataFrame(df, page_name="home"),
]

external_scripts = [
    "https://code.jquery.com/jquery-3.6.4.min.js",
    {
        "src": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha2/dist/js/bootstrap.bundle.min.js",
        "integrity": "sha384-qKXV1j0HvMUeCBQ+QVp7JcfGl760yU08IQ+GpUo5hlbpg51QRiuqHAJz8+BrxE/N",
        "crossorigin": "anonymous",
    },
]

external_stylesheets = [
    {
        "rel": "stylesheet",
        "href": "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha2/dist/css/bootstrap.min.css",
        "integrity": "sha384-aFq/bzH65dt+w6FI2ooMVUpc+21e0SRygnTpmBvdBgSdnuTN7QbdgL+OapgHtvPp",
        "crossorigin": "anonymous",
    },
]
app = Dash(
    __name__,
    # external_stylesheets=external_stylesheets,
    external_scripts=external_scripts,
)

with open(ASSETS / "index.html", "r") as f:
    app.index_string = f.read()

colors = {
    "background": "#FFFFFF",
    "text": "#7FDBFF",
}

# I should use this:
# https://davidstutz.github.io/bootstrap-multiselect/#getting-started

# @app.callback(
#     Output("weekday", "figure"),
# )
# def update_figure():
#     return make_weekday_plot(filtered_dfs)
fig = make_weekday_plot(filtered_dfs)

filter_json = {
    "minDate": date_start.strftime("%Y-%m-%d"),
    "maxDate": date_end.strftime("%Y-%m-%d"),
    "countries": df["country"].unique().sort().to_list(),
    "continents": df["continent"].unique().sort().to_list(),
    "pageNames": df["page_name"].unique().sort().to_list(),
}


@app.server.route("/filter-options", methods=["GET"])
def return_filter_json():
    print("Sending filter options")
    return jsonify(filter_json)


@app.server.route("/my-flask-route", methods=["GET", "POST"])
def test_route():
    return jsonify({"success": True})


app.layout = html.Div(
    style={"backgroundColor": colors["background"]},
    children=[
        html.Br(),
        html.Label("Smoothing"),
        dcc.Slider(
            id="smoother",
            min=0,
            max=100,
            marks={i: str(i) for i in range(0, 101, 10)},
            value=0,
        ),
        dcc.Graph(id="weekday", figure=fig),
    ],
)

if __name__ == "__main__":
    ...
    app.run_server(debug=True)

# %%
# %%
