import pandas as pd
import numpy as np
from dfsamples import df_samples
from dfextractions import df_extractions
from dfhplc import df_hplc_stat
from dash import Dash, html, dcc, Input, Output
from random import uniform
import plotly.express as px

df_gc = pd.read_excel("Entwurf.xlsx", "GC-Messungen", engine="openpyxl")
df_gc_standards = pd.read_excel("Entwurf.xlsx", "GC-Standards", engine="openpyxl")
df_gc_standards["cal HHx m corr"] = df_gc_standards["cal HHx m"] * df_gc_standards["HHx Korrekturfaktor"]
df_gc = df_gc.merge(df_gc_standards, left_on="GC-IS Nr.", right_on="GC-IS Nr.")
df_gc["m HB"] = df_gc["A HB"] / df_gc["A IS"] * df_gc["cal HB m"]
df_gc["m HHx"] = df_gc["A HHx"] / df_gc["A IS"] * df_gc["cal HHx m corr"]
df_gc = df_gc.merge(df_samples[['D5-AP Nr.', 'Inhalt', 'Versuch', 'Probenmasse [g]', 'Ausreißer Probe']],
                    left_on='D5-AP Nr.', right_on='D5-AP Nr.')
df_gc['Reinheit [%]'] = (df_gc["m HHx"] + df_gc["m HB"]) / df_gc['Probenmasse [g]']
df_gc['n HB [mol]'] = df_gc["m HB"]/86.092
df_gc['n HHx [mol]'] = df_gc["m HHx"]/114.144
df_gc['x HHx [%]'] = df_gc['n HHx [mol]'] / (df_gc["n HHx [mol]"] + df_gc["n HB [mol]"])
df_gc['x HB [%]'] = df_gc['n HB [mol]'] / (df_gc["n HHx [mol]"] + df_gc["n HB [mol]"])
df_gc = df_gc.drop(['GC-IS Nr.', 'Probenmasse [g]', 'HHx Korrekturfaktor', 'cal HHx m'], axis=1)

df_gc_stat = df_gc[(df_gc['Ausreißer Messung'] == False) & (df_gc['Ausreißer Probe'] == False)].drop(
    ['Ausreißer Messung', 'Interner Standard', 'A HB', 'A IS','A HHx', 'RT HB [min]', 'RT IS [min]', 'RT HHx [min]',
    'cal HB m', 'cal HHx m corr'], axis=1)
df_gc_stat = df_gc_stat.groupby(['Versuch', 'Inhalt'])[['m HB', 'm HHx', 'Reinheit [%]',
                                                        'n HB [mol]', 'n HHx [mol]',
                                                        'x HHx [%]', 'x HB [%]']].agg([np.mean, np.std])
df_gc_stat.columns = [f"{tup[0]} ({tup[1]})" for tup in df_gc_stat.columns]
df_gc_stat = df_gc_stat.reset_index()

if __name__ == "__main__":
    df_source_mat = df_gc_stat[df_gc_stat["Inhalt"] == "Trockene Zellen"]
    df_source_mat = df_source_mat.merge(df_hplc_stat, left_on=["Versuch", "Inhalt"], right_on=["Versuch", "Inhalt"], how="outer")
    df_source_mat = df_source_mat[df_source_mat['Inhalt'] == "Trockene Zellen"]
    df_source_mat = df_source_mat.assign(Ausgangsmaterial=df_source_mat['Versuch'])
    df_source_mat = df_source_mat.assign(Extraktionen=0)
    df_source_mat = df_source_mat.assign(Lösemittel="Keins")
    df_source_mat = df_source_mat.assign(Extraktionstemperatur=np.NaN)
    df_source_mat = df_source_mat.assign(Extraktionskonzentration=0)
    df_source_mat = df_source_mat.assign(Extraktionsdauer=np.NaN)
    df_source_mat = df_source_mat.assign(Fällungsmittel="Keins")
    df_source_mat.rename({
        "Extraktionen": "Extraktionen [n]",
        "Extraktionstemperatur": "Extraktionstemperatur [°C]",
        "Extraktionskonzentration": "Extraktionskonzentration [g/ml]",
        "Extraktionsdauer": "Extraktionsdauer [min]"
    }, inplace=True, axis=1)
    df_source_mat['Extraktionen [n]'] = df_source_mat['Extraktionen [n]'].apply(lambda x: x + uniform(-0.3, 0.3))
    df_extr = df_extractions[['Versuch', 'Inhalt', 'Urversuch',
                              'Vorextraktionen [n]', 'Lösemittel',  'Ausgansversuch',
                              'Temperatur [°C]', 'Extraktionskonzentration [g/ml]', 'Dauer [min]', 'Fällungsmittel']]
    df_extr = df_extr.merge(df_gc_stat, left_on=['Versuch', 'Inhalt'], right_on=['Versuch', 'Inhalt'])
    df_extr['Vorextraktionen [n]'] += 1
    df_extr.rename({
        "Temperatur [°C]": "Extraktionstemperatur [°C]",
        "Dauer [min]": "Extraktionsdauer [min]",
        "Vorextraktionen [n]": "Extraktionen [n]",
        "Urversuch": "Ausgangsmaterial"
    }, inplace=True, axis=1)
    df_extr = df_extr.merge(df_hplc_stat, left_on=["Versuch", "Inhalt"], right_on=["Versuch", "Inhalt"], how="outer")
    df_extr = df_extr[df_extr['Inhalt'] != "Fällungsüberstand"]
    df_final = pd.concat([df_source_mat, df_extr], ignore_index=True)
    df_final = df_final[df_final['Reinheit [%] (std)'] < 0.1]
    df_final = df_final[df_final['x HHx [%] (std)'] < 0.04]

    # jitter
    df_final['Extraktionen [n]'] = df_final['Extraktionen [n]'].apply(lambda x: x + uniform(-0.3, 0.3))
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, "display.width", 800):
        # print(df_final)
        pass
    fig1 = px.scatter(df_final,
                      x="Extraktionen [n]",
                      y='x HHx [%] (mean)',
                      error_y='x HHx [%] (std)',
                      color="Inhalt",
                      symbol='Ausgangsmaterial',
                      hover_name="Versuch",
                      hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                    'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
    fig2 = px.scatter(df_final,
                      x="Extraktionen [n]",
                      y='Reinheit [%] (mean)',
                      error_y='Reinheit [%] (std)',
                      color="Inhalt",
                      symbol='Ausgangsmaterial',
                      hover_name="Versuch",
                      hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                  'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
    fig3 = px.scatter(df_final,
                      x="Extraktionen [n]",
                      y='Mw (mean)',
                      error_y='Mw (std)',
                      color="Inhalt",
                      symbol='Ausgangsmaterial',
                      hover_name="Versuch",
                      hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                  'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
    app = Dash(__name__)
    app.layout = html.Div(children=[
        html.Label('Lösemittel:'),
        dcc.Dropdown(df_final['Lösemittel'].unique(), "Aceton", id='solvent-filter', multi=True),
        html.Br(),

        html.Label('Fällungsmittel:'),
        dcc.Dropdown(df_final['Fällungsmittel'].unique(), "Isopropanol", id='reciprocent-filter', multi=True),
        html.Br(),

        html.Label('Ausgangsmaterial:'),
        dcc.Dropdown(df_final['Ausgangsmaterial'].unique(), [
            "100 L-6",
            "100 L-7",
            "I.22.0160",
            "I.22.0161",
            "I.22.0162"
        ], id='source-filter', multi=True),
        html.Br(),

        html.Label('Extraktionstemperatur [°C]:'),
        dcc.RangeSlider(
            id='temp-slider',
            min=df_final['Extraktionstemperatur [°C]'].min(), max=df_final['Extraktionstemperatur [°C]'].max(), step=1,
            value=[df_final['Extraktionstemperatur [°C]'].min(), df_final['Extraktionstemperatur [°C]'].max()]
        ),
        html.Br(),

        html.Label('Extraktionskonzentration [g/ml]:'),
        dcc.RangeSlider(
            id='conc-slider',
            min=df_final['Extraktionskonzentration [g/ml]'].min(), max=df_final['Extraktionskonzentration [g/ml]'].max(),
            step=0.01,
            value=[df_final['Extraktionskonzentration [g/ml]'].min(), df_final['Extraktionskonzentration [g/ml]'].max()]
        ),
        html.Br(),

        html.Label('Extraktionsdauer [min]:'),
        dcc.RangeSlider(
            id='dur-slider',
            min=df_final['Extraktionsdauer [min]'].min(),
            max=df_final['Extraktionsdauer [min]'].max(), step=5,
            value=[df_final['Extraktionsdauer [min]'].min(), df_final['Extraktionsdauer [min]'].max()]
        ),
        html.Br(),

        dcc.Graph(
            figure=fig1,
            id="HHx-plot"
        ),
        dcc.Graph(
            figure=fig2,
            id="Pur-plot"
        ),
        dcc.Graph(
            figure=fig3,
            id="Mw-plot"
        )
    ])


    def get_lines(df, trail):
        with pd.option_context('display.max_rows', None, 'display.max_columns', None, "display.width", 800):
            print(trail)
            # print(df)
            acc = df[df['Versuch'] == trail['points'][0]['hovertext']]
            tmp = acc
            while not tmp.empty:
                tmp = df[df['Versuch'].isin(tmp['Ausgansversuch'])]
                acc = pd.concat([acc, tmp], ignore_index=True)
            print(acc)


    @app.callback(
        Output('HHx-plot', 'figure'),
        Output('Pur-plot', 'figure'),
        Output('Mw-plot', 'figure'),
        Input('solvent-filter', 'value'),
        Input('reciprocent-filter', 'value'),
        Input('source-filter', 'value'),
        Input('temp-slider', 'value'),
        Input('conc-slider', 'value'),
        Input('dur-slider', 'value'),
        Input('HHx-plot', 'hoverData'),
    )
    def callback(solvents, reciprocents, source, temp_range, concentration_range, duration_range, hhx_hover):
        if isinstance(solvents, str):
            solvents = [solvents]
        df_tmp = df_final[df_final['Lösemittel'].isin(solvents)]
        if isinstance(reciprocents, str):
            reciprocents = [reciprocents]
        df_tmp = df_tmp[df_tmp['Fällungsmittel'].isin(reciprocents)]
        if isinstance(source, str):
            source = [source]
        df_tmp = df_tmp[df_tmp['Ausgangsmaterial'].isin(source)]
        df_tmp = df_tmp[df_tmp['Extraktionstemperatur [°C]'].between(*temp_range)]
        df_tmp = df_tmp[df_tmp['Extraktionskonzentration [g/ml]'].between(*concentration_range)]
        df_tmp = df_tmp[df_tmp['Extraktionsdauer [min]'].between(*duration_range)]
        df_tmp = pd.concat([df_source_mat, df_tmp], ignore_index=True)

        if hhx_hover is not None:
            get_lines(df_tmp[['Versuch', 'Inhalt', 'Ausgansversuch', 'Extraktionen [n]',
                              'Reinheit [%] (mean)', 'x HHx [%] (mean)', 'Mw (mean)']], hhx_hover)

        fig1 = px.scatter(df_tmp,
                          x="Extraktionen [n]",
                          y='x HHx [%] (mean)',
                          error_y='x HHx [%] (std)',
                          color="Inhalt",
                          symbol='Ausgangsmaterial',
                          hover_name="Versuch",
                          hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                      'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
        fig2 = px.scatter(df_tmp,
                          x="Extraktionen [n]",
                          y='Reinheit [%] (mean)',
                          error_y='Reinheit [%] (std)',
                          color="Inhalt",
                          symbol='Ausgangsmaterial',
                          hover_name="Versuch",
                          hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                      'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
        fig3 = px.scatter(df_tmp,
                          x="Extraktionen [n]",
                          y='Mw (mean)',
                          error_y='Mw (std)',
                          color="Inhalt",
                          symbol='Ausgangsmaterial',
                          hover_name="Versuch",
                          hover_data=['Lösemittel', 'Extraktionstemperatur [°C]',
                                      'Extraktionskonzentration [g/ml]', 'Fällungsmittel'])
        return fig1, fig2, fig3

    app.run_server(debug=True)


df_gc = df_gc.drop(columns=['Ausreißer Probe'])
