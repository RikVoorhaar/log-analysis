# %%
from pathlib import Path

import plotly.express as px
import polars as pl
from dash import Dash, Input, Output, dcc, html

from log_parsing.database_def import TableNames
from log_parsing.parse_access_log import load_df_from_db
import flask
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

external_stylesheets = [
    {
        "rel": "stylesheet",
        "href": "https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/css/bootstrap.min.css",
        "integrity": "sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T",
        "crossorigin": "anonymous",
    }
]
app = Dash(__name__, external_stylesheets=external_stylesheets)

with open(ASSETS / "index.html", "r") as f:
    app.index_string = f.read()

colors = {
    "background": "#FFFFFF",
    "text": "#7FDBFF",
}


# @app.callback(
#     Output("weekday", "figure"),
# )
# def update_figure():
#     return make_weekday_plot(filtered_dfs)
fig = make_weekday_plot(filtered_dfs)


@app.server.route("/my-flask-route")
def test_route():
    print("hello!")
    return {"message": "hey"}


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
    app.run_server(debug=True)
