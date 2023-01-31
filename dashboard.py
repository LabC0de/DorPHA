from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import numpy as np

from dfextractions import df_extractions
from dfgc import df_gc, df_gc_stat
from dfhplc import df_hplc_results
from dfsamples import df_samples


app = Dash(__name__)


class Dataset:
    dataframes = {}
    cat_columns = {}
    num_columns = {}
    @staticmethod
    def edge_case_clean(str):
        if str is None:
            return None
        if str.find("Inhalt") != -1:
            return "Inhalt"
        elif str.find("Versuch") != -1:
            return "Versuch"
        else:
            return str

    @staticmethod
    def dict_o_lists_to_str(dict):
        acc = []
        for dataframe, columns in dict.items():
            for column in columns:
                acc.append(f"{dataframe}: {column}")
        return acc

    @staticmethod
    def get_numerical_columns():
        return Dataset.dict_o_lists_to_str(Dataset.num_columns)

    @staticmethod
    def get_categorical_columns():
        return Dataset.dict_o_lists_to_str(Dataset.cat_columns)

    @staticmethod
    def set_df(name, df):
        Dataset.num_columns[name] = list(df.select_dtypes(include=[np.number]).columns.values)
        Dataset.cat_columns[name] = list(df.select_dtypes(exclude=[np.number]).columns.values)
        Dataset.dataframes[name] = df

    @staticmethod
    def get_df(*args):
        dfs = {}
        for arg in args:
            if arg is None:
                continue
            df, col = arg.split(": ")
            if df in dfs.keys():
                dfs[df].add(col)
            else:
                dfs[df] = {'Inhalt', 'Versuch', col}
        dfs = sorted(dfs.items(), key=lambda item: Dataset.dataframes[item[0]].shape[0], reverse=True)
        ret = Dataset.dataframes[dfs[0][0]]
        ret = ret[dfs[0][1]].dropna()
        ret.columns = [f"{dfs[0][0]}: {col}" if col not in ['Versuch', 'Inhalt'] else col for col in ret.columns]
        for df, cols in dfs[1:]:
            tmp = Dataset.dataframes[df]
            tmp = tmp[cols].dropna()
            tmp.columns = [f"{df}: {cl}" if cl not in ['Versuch', 'Inhalt'] else cl for cl in tmp.columns]
            ret = ret.merge(tmp, left_on=['Versuch', 'Inhalt'], right_on=['Versuch', 'Inhalt'])
        return ret

    def __init__(self):
        df_extractions_raw = df_extractions
        self.set_df('Extraktionen', df_extractions_raw)

        df_samples_raw = df_samples
        self.set_df('Analytikproben', df_samples_raw)

        df_gc_results_raw = df_gc
        self.set_df('GC Ergebnisse', df_gc_results_raw)

        df_gc_results = df_gc_stat
        self.set_df('GC Ergebnisse (Stat)', df_gc_results)

        df_hplc_results_raw = df_hplc_results
        self.set_df('HPLC Ergebnisse', df_hplc_results_raw)


data = Dataset()


def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


fig = px.scatter_3d(df_extractions,
                    x='Extraktionskonzentration [g/ml]',
                    y='Fällungskonzentration [g/ml]',
                    z='Masse [g]', color='Lösemittel')

app.layout = html.Div(children=[
    html.Button("3D Scatter Plot", id="3DScatterCollapse", className="collapsible"),
    html.Div(children=[
    html.Div(children=[
        dcc.Graph(figure=fig, id='indicator-graphic',
                  style={"height": "100%", "width": "100%"}),
    ], style={'padding': 1, "width": "66%", "border": "1px solid black"}),
    html.Div(children=[
        html.Label('X:'),
        dcc.Dropdown(Dataset.get_numerical_columns(), "GC Ergebnisse: x HHx [%]", id='xaxis-column'),
        html.Br(),

        html.Label('Y:'),
        dcc.Dropdown(Dataset.get_numerical_columns(), "HPLC Ergebnisse: Mw", id='yaxis-column'),
        html.Br(),

        html.Label('Z:'),
        dcc.Dropdown(Dataset.get_numerical_columns(), "GC Ergebnisse: Reinheit [%]", id='zaxis-column'),
        html.Br(),

        html.Label('Color:'),
        dcc.Dropdown(["None"] + Dataset.get_numerical_columns() + Dataset.get_categorical_columns(), "None", id='color-column'),
        html.Br(),

        html.Label('Size:'),
        dcc.Dropdown(["None"] + Dataset.get_numerical_columns(), "None", id='size-column'),
        html.Br(),

        html.Label('Of interest:'),
        dcc.Dropdown(Dataset.get_numerical_columns() + Dataset.get_categorical_columns(), multi=True, id='interest-column'),
        html.Br()
    ], style={'padding': 1, 'flex': 1, "width": "33vw", "border": "1px solid black"}),
], id="3DScatterContent", className="content", style={})
    ]
)


@app.callback(
    Output(component_id='3DScatterContent', component_property='style'),
    State('3DScatterContent', 'style'),
    Input('3DScatterCollapse', 'n_clicks')
)
def collapse3dscatter(style, n_clicks):
    print(style, n_clicks)
    if n_clicks is None:
        raise PreventUpdate
    if n_clicks % 2 == 0:
        style.pop("max-height", None)
    else:
        style["max-height"] = 0
    return style


@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'),
    Input('zaxis-column', 'value'),
    Input('color-column', 'value'),
    Input('size-column', 'value'),
    Input('interest-column', 'value'),
)
def update(xaxis_column_name, yaxis_column_name, zaxis_column_name, color_column_name, size_column_name, interesting_columns):
    if size_column_name == "None":
        size_column_name = None
    if color_column_name == "None":
        color_column_name = None
    if interesting_columns is not None:
        df = Dataset.get_df(xaxis_column_name, yaxis_column_name, zaxis_column_name, color_column_name, size_column_name,
                            *interesting_columns)
    else:
        df = Dataset.get_df(xaxis_column_name, yaxis_column_name, zaxis_column_name, color_column_name, size_column_name)
    fig = px.scatter_3d(df, x=xaxis_column_name, y=yaxis_column_name, z=zaxis_column_name,
                        color=Dataset.edge_case_clean(color_column_name), size=size_column_name,
                        hover_name="Versuch", hover_data=interesting_columns)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
