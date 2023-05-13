from dash import Dash, html, dcc, Input, Output, State
import webbrowser
from utils import *

import sys

path = None
if len(sys.argv) > 1:
    path = sys.argv[1]

# Load data
df = get_data(path)
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
    labels = ["הכל"] + [f'{name}  כ-{cnts:,.0f}' for name, cnts in sub_model_cnts.items()]
    values = ["ALL"] + sub_model_cnts.index.tolist()
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
        html.Label("Select a sub - model"),
        dcc.Dropdown(id="sub-model-dropdown",
                     options=sub_model_options,
                     disabled=False,
                     clearable=False,
                     multi=False,  # Add multi here
                     value="ALL"),
        html.Label("Color by"),
        dcc.RadioItems(['year', 'sub_model'], 'year', id="radio-color", inline=True),
        html.Label(str(df['date_updated'].max()), style={"direction": "ltr", "margin-top": "300px"})
    ],
)

# Define content area
content = html.Div(
    className="content",
    children=[
        dcc.Graph(id="scatter-plot", style={"height": "80vh"}),
        html.Label(children=[], id="output-text"),
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

state = {"prev_model": selected_model}


# Define callback to update scatter plot
@app.callback(Output("scatter-plot", "figure"), Output("sub-model-dropdown", "options"),
              Output("sub-model-dropdown", "value"),
              [Input("model-dropdown", "value"), Input("sub-model-dropdown", "value"), Input("radio-color", "value")])
def update_scatter_plot(selected_model, selected_sub_model, color_by):
    df_q = filter_df(selected_model)
    sub_model_options = generate_sub_models(df_q)
    if selected_sub_model != "ALL":
        if state['prev_model'] != selected_model:
            selected_sub_model = "ALL"
        else:
            df_q = df_q[df_q['sub_model'] == selected_sub_model]
    fig = get_graph(df_q, selected_model, color_by)
    fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
    fig.update_traces(hoverlabel=dict(align="right"))
    fig.update_traces(marker=dict(size=8, line=dict(width=0.8, color='DarkSlateGrey')),
                      selector=dict(mode='markers'))
    state['prev_model'] = selected_model
    return fig, sub_model_options, selected_sub_model


@app.callback(Output("output-text", "children"), [Input("scatter-plot", "clickData")])
def click_event(click_data):
    if click_data:
        point = click_data['points'][0]
        link = point['customdata'][1]
        webbrowser.open(link)
        return [str(point)]
    return []


# Run app
if __name__ == "__main__":
    app.run_server(debug=True)
