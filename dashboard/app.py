from pathlib import Path
import os
import logging
from time import perf_counter
from functools import wraps

import plotly.express as px
from flask import Flask, jsonify, request, send_from_directory, make_response
from pydantic import ValidationError, parse_obj_as

# from dash import Dash, Input, Output, dcc, html
from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db
from log_parsing.plot_functions import (
    FilterModel,
    plot_functions,
)
from log_parsing.config import logger


DIST = Path(__file__).parent / "dist"
PUBLIC = Path(__file__).parent / "public"
PLOT_COLOR_SCHEME = px.colors.qualitative.T10


app = Flask(__name__, static_folder=PUBLIC)
app.config.update(
    SERVER_NAME = os.environ.get("FLASK_SERVER_NAME", "localhost"),
    SECRET_KEY=os.environ["FLASK_SECRET_KEY"],
)

# app.testing = True
# app.debug = True
# app.logger.setLevel(logging.DEBUG)

df = load_df_from_db(TableNames.PAGES_LOG)
date_start = df["time"].min()
date_end = df["time"].max()


filter_json = {
    "minDate": date_start.strftime("%Y-%m-%d"),
    "maxDate": date_end.strftime("%Y-%m-%d"),
    "countries": df["country"].unique().sort().to_list(),
    "continents": df["continent"].unique().sort().to_list(),
    "pageNames": df["page_name"].unique().sort().to_list(),
}


def route_with_time_taken(rule, methods=None):
    if methods is None:
        methods = ["GET"]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time_before = perf_counter()
            result = func(*args, **kwargs)
            remote_addr = request.remote_addr
            time_taken_ms = (perf_counter() - time_before) * 1000
            logger.info(
                f"request {rule} from {remote_addr} took {time_taken_ms:.2f} ms"
            )
            return result

        app.add_url_rule(rule, func.__name__, wrapper, methods=methods)
        return wrapper

    return decorator


# @route_with_time_taken("/all-plots/")
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


# @app.route("/filter-data/", methods=["GET", "POST"])
@route_with_time_taken("/filter-data/", methods=["GET", "POST"])
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
    filter_lengths = [len(df.dataframe) for df in filtered_dfs]
    filtered_dfs = [df for df in filtered_dfs if len(df.dataframe) > 0]
    if len(filtered_dfs) == 0:
        logger.info("All filters are empty")
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

    return_data = jsonify(
        {
            "plots": {
                plot_id: plot_function(filtered_dfs).to_json()
                for plot_id, plot_function in plot_functions.items()
            },
            "filters": filter_lengths,
        }
    )

    return return_data


@app.route("/")
def index():
    return send_from_directory(PUBLIC, "index.html")


@app.route("/dist/<path:path>")
def dist(path):
    return send_from_directory(DIST, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
