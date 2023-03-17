# %%
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

app = Dash(__name__)

colors = {
    "background": "#FFFFFF",
    "text": "#7FDBFF",
}

df = pd.read_csv("date_hour_count.csv", index_col=0, parse_dates=True)


@app.callback(
    Output("requests", "figure"),
    Input("smoother", "value"),
)
def update_figure(smoother: float):
    if smoother == 0:
        df_smooth = df
    else:
        df_smooth = df.rolling(int(smoother)).mean()

    fig = px.line(df_smooth, x=df_smooth.index, y="time_iso8601")
    return fig


app.layout = html.Div(
    style={"backgroundColor": colors["background"]},
    children=[
        html.Div(
            children="Number of requests per hour.",
            style={
                "color": colors["text"],
                "font-family": "sans-serif",
                "font-size": "30px",
            },
        ),
        html.Br(),
        html.Label("Smoothing"),
        dcc.Slider(
            id="smoother",
            min=0,
            max=100,
            marks={i: str(i) for i in range(0, 101, 10)},
            value=0,
        ),
        dcc.Graph(id="requests"),
    ],
)

x = 4

if __name__ == "__main__":
    app.run_server(debug=True)
