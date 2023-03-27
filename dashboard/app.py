# %%
from pathlib import Path

import plotly.express as px
import polars as pl
from dash import Dash, Input, Output, dcc, html

from log_parsing.database_def import TableNames
from pydantic import parse_obj_as, ValidationError
from log_parsing.parse_access_log import load_df_from_db
from flask import request, jsonify
from log_parsing.plot_functions import FilteredDataFrame, make_weekday_plot, FilterModel

ASSETS = Path(__file__).parent / "assets"

df = load_df_from_db(TableNames.PAGES_LOG)
date_start = df["time"][0]
date_end = df["time"][-1]
filtered_dfs = [
    FilteredDataFrame(df),
    FilteredDataFrame(df, continents=["Europe", "Asia"]),
    FilteredDataFrame(df, countries=["Denmark", "Sweden"]),
    FilteredDataFrame(df, page_names=["home"]),
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


@app.server.route("/filter-data", methods=["GET", "POST"])
def parse_filters():
    request_json = request.get_json()
    try:
        filter_list = parse_obj_as(list[FilterModel], request_json)
    except ValidationError:
        print("Invalid filter")
        print(request_json)
        return jsonify({"success": False})
    filtered_dfs = [filter.to_filtered_data_frame(df) for filter in filter_list]
    with app.server.app_context():
        fig = make_weekday_plot(filtered_dfs)
        app.layout.children[1].figure = fig

    return jsonify({"success": True})


# we need a way to update the figures through a callback or not
# one stupid way is to use the interval element as trigger


app.layout = html.Div(
    style={"backgroundColor": colors["background"]},
    children=[
        html.Br(),
        dcc.Graph(id="weekday", figure=fig),
    ],
)

if __name__ == "__main__":
    app.run_server(debug=True)

# %%
# %%
