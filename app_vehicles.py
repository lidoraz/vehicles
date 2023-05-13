import dash
from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import webbrowser
from utils import *

import sys

path = None
if len(sys.argv) > 1:
    path = sys.argv[1]

# Load data
df = get_data(path)
updated_at = df.attrs["date_updated"] if "date_updated" in df.attrs else str(df["date_updated"].max())
model_cnts = get_counts(df)
labels = [f'{name[0]} - {name[1]}, כ-{cnts:,.0f}' for name, cnts in model_cnts.items()]
values = [name[1] for name in model_cnts.index]
import random

selected_model = random.choice(values[:10])


def filter_df(selected_model):
    df_q = df.query(f"""model == "{selected_model}" and kilometers < 500000 and 1000 < price < 3000000""").copy()
    return df_q


def generate_sub_models(df_q):
    # sub_model_cnts = df_q['sub_model'].value_counts()
    sub_model_cnts = \
        df_q.groupby("sub_model").agg({"year": "max", "model": "size"}).sort_values(by=["year", "model"],
                                                                                    ascending=False)[
            'model']
    labels = [f'{name}  כ-{cnts:,.0f}' for name, cnts in sub_model_cnts.items()]
    values = sub_model_cnts.index.tolist()
    options = [{"label": label, "value": value} for label, value in zip(labels, values)]
    return options


sub_model_options = generate_sub_models(filter_df(selected_model))

# Initialize app
# app = Dash(external_stylesheets=[dbc.themes.CYBORG])
app = Dash()

# Define sidebar
sidebar = html.Div(
    className="sidebar",
    children=[
        html.H2("Vehicle Explorer"),
        html.Hr(),
        html.Label("Select a model"),
        dcc.Dropdown(
            id="model-dropdown",
            options=[{"label": label, "value": value} for label, value in zip(labels, values)],
            value=selected_model,
            clearable=False,
        ),
        html.Label("Color by"),
        dcc.RadioItems(['year', 'sub_model'], 'year', id="radio-color", inline=True),
        html.Label("Select a sub-model"),
        html.Div([dbc.Button("Clear / All", id="sub-model-clear"),
                  dbc.Checklist(sub_model_options,
                                value=[x['value'] for x in sub_model_options],
                                id="sub-model-dropdown")], className="sub-model-cont"),
        html.Label(updated_at, className="footer-text"),
        html.Label("", id="graph-link")
    ],
)

# Define content area
content = html.Div(
    className="content",
    children=[
        dcc.Graph(id="scatter-plot", style={"height": "80vh"}),
        html.Label(children="", id="output-text", style=dict(direction="ltr")),
    ],
)

# Define app layout
app.layout = html.Div(
    className="container",
    children=[
        sidebar,
        content,
    ],
)

state = {"prev_model": selected_model, "clear_n_clicks": 0}


# Define callback to update scatter plot
@app.callback(Output("scatter-plot", "figure"), Output("sub-model-dropdown", "options"),
              Output("sub-model-dropdown", "value"), Output("sub-model-clear", "n_clicks"),
              [Input("model-dropdown", "value"),
               Input("sub-model-dropdown", "value"),
               Input("radio-color", "value"),
               Input("sub-model-clear", "n_clicks")
               ])
def update_scatter_plot(selected_model, selected_sub_models, color_by, clear_n_clicks):
    df_q = filter_df(selected_model)
    sub_model_options = generate_sub_models(df_q)
    if clear_n_clicks:
        if len(selected_sub_models):
            selected_sub_models = []
        else:
            selected_sub_models = [x['value'] for x in sub_model_options]
        return dash.no_update, sub_model_options, selected_sub_models, 0

    dff = df_q[df_q['sub_model'].isin(selected_sub_models)]
    if len(dff):
        df_q = dff
    else:
        selected_sub_models = [x['value'] for x in sub_model_options]

    fig = get_graph(df_q, selected_model, color_by)
    fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    fig.update_traces(hoverlabel=dict(align="right"))
    fig.update_traces(marker=dict(size=8, line=dict(width=0.8, color='DarkSlateGrey')),
                      selector=dict(mode='markers'))
    state['prev_model'] = selected_model
    return fig, sub_model_options, selected_sub_models, 0


@app.callback(Output("output-text", "children"), Output("graph-link", "children"), [Input("scatter-plot", "clickData")])
def click_event(click_data):
    if click_data:
        point = click_data['points'][0]
        link = point['customdata'][2]
        # webbrowser.open(link)
        id_ = link.split('/')[-1]
        item = df.query(f"id=='{id_}'").squeeze().to_dict()
        # item = html.Div([[] for k,v in item.items()])
        item = ""
        return str(item), html.A("CLICK TO AD", href=link, target="_blank")
    return "", ""


# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
