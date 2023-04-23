# %%
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, jsonify, request, send_from_directory, make_response
from pydantic import ValidationError, parse_obj_as

# from dash import Dash, Input, Output, dcc, html
from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db
from log_parsing.plot_functions import (
    FilterModel,
    plot_functions,
)

DIST = Path(__file__).parent / "dist"
PUBLIC = Path(__file__).parent / "public"
PLOT_COLOR_SCHEME = px.colors.qualitative.T10

app = Flask(__name__, static_folder=PUBLIC)
app.config["PROPAGATE_EXCEPTIONS"] = True

df = load_df_from_db(TableNames.PAGES_LOG)
date_start = df["time"][0]
date_end = df["time"][-1]


filter_json = {
    "minDate": date_start.strftime("%Y-%m-%d"),
    "maxDate": date_end.strftime("%Y-%m-%d"),
    "countries": df["country"].unique().sort().to_list(),
    "continents": df["continent"].unique().sort().to_list(),
    "pageNames": df["page_name"].unique().sort().to_list(),
}


@app.route("/all-plots/")
def all_plot_ids():
    return jsonify(list(plot_functions.keys()))


@app.route("/filter-options", methods=["GET"])
def return_filter_json():
    print("Sending filter options")
    return jsonify(filter_json)


@app.route("/colors", methods=["GET"])
def return_colors():
    return jsonify(PLOT_COLOR_SCHEME)


@app.route("/filter-data/", methods=["GET", "POST"])
def parse_filters():
    request_json = request.get_json()
    try:
        filter_list = parse_obj_as(list[FilterModel], request_json)
    except ValidationError:
        print("Invalid filter")
        print(request_json)
        return jsonify({"success": False})
    filtered_dfs = [
        filter.to_filtered_data_frame(df, colors=PLOT_COLOR_SCHEME)
        for filter in filter_list
    ]
    filtered_dfs = [df for df in filtered_dfs if len(df.dataframe) > 0]
    if len(filtered_dfs) == 0:
        response = make_response(
            jsonify(
                {
                    "success": False,
                    "message": "All filters are empty",
                    "error_code": "EMPTY_FILTERS",
                }
            ),
            400,
        )
        return response

    graphs: dict[str, go.Figure] = {
        plot_id: plot_function(filtered_dfs)
        for plot_id, plot_function in plot_functions.items()
    }

    graphs_json: dict[str, str] = {
        plot_id: graph.to_json() for plot_id, graph in graphs.items()
    }

    return jsonify(graphs_json)


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/dist/<path:path>")
def dist(path):
    print(path)
    return send_from_directory(DIST, path)


if __name__ == "__main__":
    app.run()
