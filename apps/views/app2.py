import dash_core_components as dcc
import dash_html_components as html
import dash_table
import dash
from dash.dependencies import Input, Output, ClientsideFunction, State
import pandas as pd
from datetime import datetime as dt
import pathlib
import plotly.graph_objs as go
from app import app
import dash_bootstrap_components as dbc
from pandas import DataFrame

qub_logo = "../assets/qub2.jpg"
server = app.server
app.config.suppress_callback_exceptions = True
# Path
BASE_PATH = pathlib.Path(__file__).parent.resolve()
DATA_PATH = BASE_PATH.joinpath("../../data").resolve()

# Read data
df = pd.read_csv(DATA_PATH.joinpath("admissions.csv"))

clinic_list = df["admission_type"].unique().tolist()
# Date
# Format checkin Time
df["Check-In Time"] = df["admittime"].apply(
    lambda x: dt.strptime(x, "%d/%m/%Y %H:%M")
)  # String -> Datetime

# Format discharge time
df["Discharge Time"] = df["dischtime"].apply(
    lambda x: dt.strptime(x, "%d/%m/%Y %H:%M")
)  # String -> Datetime

# Format length of stay in ICU LOS -midnight
delta = (df["Discharge Time"] - df["Check-In Time"])
df["Length of Stay"] = delta.dt.days
filtered_df = df

modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(id="modal-header"),
                dbc.ModalBody(id="modal-content"),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close", className="ml-auto")
                ),
            ],
            id="modal",
        ),
    ]
)


def description_card():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.H5("ICU Analytics"),
            html.H3("Welcome to the ICU Analytics Dashboard for Royal Victoria Hospital"),
            html.Div(
                id="intro",
                children=["Search patients by admission type, check-in date and diagnosis.", html.Br(),
                          "Click on a patient to view more information."]
            ),
        ],
    )


def generate_control_card():
    """
    :return: A Div containing controls for filtering.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P("Select Admission Type"),
            dcc.Dropdown(
                id="clinic-select",
                options=[{"label": i, "value": i} for i in clinic_list],
                value=clinic_list[:],
                multi=True
            ),
            html.P("Select Check-In Time"),
            dcc.DatePickerRange(
                id="date-picker-select",
                start_date=dt(2100, 7, 4),
                end_date=dt(2200, 1, 15),
                min_date_allowed=dt(2000, 1, 1),
                max_date_allowed=dt(2200, 12, 31),
                initial_visible_month=dt(2100, 7, 4),
                display_format="DD-MM-YYYY"
            ),
            html.P("Search Diagnosis"),
            dcc.Input(
                id="diagnosis-select",
                type="text",
                placeholder="Enter diagnosis...",
            ),
            html.Br(),
            html.Br(),
            html.Div(id='patient-count'),
        ],
    )


def generate_table():
    return dash_table.DataTable(
        id='patient-table',
        columns=[
            {'name': 'Patient ID', 'id': 'subject_id'},
            {'name': 'Admission Date', 'id': 'admittime', 'type': 'datetime'},
            {'name': 'Discharge Date', 'id': 'dischtime', 'type': 'datetime'},
            {'name': 'Length of Stay', 'id': 'Length of Stay', 'type': 'numeric'},
            {'name': 'Admission Type', 'id': 'admission_type'},
            {'name': 'Diagnosis', 'id': 'diagnosis'},
        ],
        style_header={'backgroundColor': 'white',
                      'fontWeight': 'bold'},
        fixed_rows={'headers': True},
        style_cell={
            'height': 'auto',
            # all three widths are needed
            'minWidth': '80px',
            'width': '140px',
            'maxWidth': '140px',
            'whiteSpace': 'normal',
            'border': '4px',
            'font-family': 'Courier New',
        },
        style_cell_conditional=[
            {'if': {'column_id': 'subject_id'},
             'width': '10%'}
        ],
        page_size=20,
        style_data_conditional=[{
            'if': {'row_index': 'odd'},
            'backgroundColor': '#E5E7E9',
        }],
        style_table={'overflowX': 'auto'},
        data=df.to_dict("rows"),
        export_format="csv",
    )


layout = html.Div(
    id="app-container",
    children=[
        # Left column
        html.Div(
            id="page",
            className="four columns",
            children=[description_card(), generate_control_card()]
                     + [
                         html.Div(
                             ["initial child"], id="output-clientside", style={"display": "none"}
                         )
                     ],
        ),
        html.Div(
            id="table-column",
            className="eight columns",
            children=[
                dcc.Loading(generate_table()),
                # html.Button(
                #     "Print",
                #     id="table-print"
                # ),
            ],
        ),
        modal
    ]
)


@app.callback(
    Output("patient-table", "data"),
    Output('patient-count', 'children'),
    Output('patient-table', 'page_current'),
    [
        Input("clinic-select", "value"),
        Input("date-picker-select", "start_date"),
        Input("date-picker-select", "end_date"),
        Input('diagnosis-select', 'value'),
    ],
)
def update_table(admission_type, start, end, diagnosis):
    start = start + " 00:00:00"
    end = end + " 00:00:00"
    global filtered_df
    if admission_type is not None:
        filtered_df = df[
            (df["admission_type"].isin(admission_type))
        ]
    if diagnosis is not None:
        filtered_df = filtered_df[
            filtered_df.apply(lambda row: row.str.contains(diagnosis, regex=False, case=False).any(), axis=1)]

    filtered_df = filtered_df.sort_values("Check-In Time").set_index("Check-In Time")[
                  start:end
                  ]

    data = filtered_df.to_dict("rows")
    count = len(data)
    return data, html.H4('Patient Count: {}'.format(count)), 0


@app.callback(Output('modal', 'is_open'),
              [Input('patient-table', 'active_cell'),
               Input('close', 'n_clicks')],
              [State("modal", "is_open")])
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# get modal for patient clicked in table
@app.callback(Output('modal-header', 'children'),
              [Input('patient-table', 'active_cell'),
               Input('patient-table', 'data'),
               Input('close', 'n_clicks'),
               Input('patient-table', "page_current"),
               Input('patient-table', "page_size")
               ],
              )
def update_graph(active_cell, data, n_clicks, page_current, page_size):
    records = filtered_df.iloc[
              page_current * page_size:(page_current + 1) * page_size
              ].to_dict('records')
    if active_cell is not None:
        row = records[active_cell['row']]
        patient = row['subject_id']
        patient = "Patient ID: " + str(patient)
        return patient


# modal callback
@app.callback(Output('modal-content', 'children'),
              [Input('patient-table', 'active_cell'),
               Input('close', 'n_clicks')
               ],
              )
def update_graph(active_cell, n_clicks):
    if active_cell is not None:
        return dcc.Tabs(id="patient-tabs", value='tab-1', children=[
            dcc.Tab(label='Patient Details', value='tab-1'),
            # dcc.Tab(label='Patient Readings', value='tab-2'),
        ]), html.Div(id='tabs-content')


# modal content callback
@app.callback(Output('tabs-content', 'children'),
              [Input('patient-tabs', 'value'),
               Input('patient-table', 'active_cell'),
               Input('patient-table', "page_current"),
               Input('patient-table', "page_size")
               ], )
def render_content(tab, active_cell, page_current, page_size):
    records = filtered_df.iloc[
              page_current * page_size:(page_current + 1) * page_size
              ].to_dict('records')
    if active_cell is not None:
        row = records[active_cell['row']]
        if tab == 'tab-1':
            return html.Div([
                html.H4("Admission Date: "), html.P(row["admittime"]),
                html.H4("Admission Type: "), html.P(row['admission_type']),
                html.H4("Discharge Date: "), html.P(row['dischtime']),
                html.H4("Discharge Location: "), html.P(row['discharge_location']),
                html.H4("Length of Stay: "), html.P(row["Length of Stay"]),
                html.H4("Diagnosis: "), html.P(row['diagnosis']),
            ])
        # elif tab == 'tab-2':
        #     fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])
        #     return html.Div([
        #         # html.H3('Patient Readings'),
        #         html.P('This is where the patients readings will go'),
        #         dcc.Graph(
        #             id='example-graph-2',
        #             figure=fig
        #         )
        #     ])


# @app.callback(
#     Output('las-table-print', 'children'),
#     [Input('table-print', 'n_clicks'),
#      Input('patient-table', 'data')]
# )
# def update_table_print(n_clicks, data):
#     if n_clicks is None:
#         return dash.no_update
#     else:
#         tables_list = []
#         num_tables = int(len(data) / 20) + 1  # 20 rows max per page
#         for i in range(num_tables):
#             table_rows = []
#             for j in range(20):
#                 if i * 20 + j >= len(data):
#                     break
#                 table_rows.append(html.Tr([
#                     html.Td(
#                         data[i * 20 + j][key],
#                     ) for key in data[0].keys()]))
#             table_rows.insert(0, html.Tr([
#                 html.Th(
#                     key,
#                 ) for key in data[0].keys()]))
#             tables_list.append(
#                 html.Div(className='tablepage', children=html.Table(table_rows)))
#         return tables_list
