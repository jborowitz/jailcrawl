# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pathlib
import plotly.graph_objs as go

# import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import dash_table
import numpy as np
import plotly.figure_factory as ff
import plotly.express as px
import pickle
# import matplotlib.pyplot as plt
import io
import base64
app = dash.Dash(
        __name__,
        meta_tags=[{"name": "viewport", "content": "width=device-width"}],
        suppress_callback_exceptions=True
        )
server = app.server

app.layout = html.Div(
        [
            html.P("Hello!")
            ])
#             Header(app),
#             # page 2
#             # html.Div(
#             dcc.Tabs(
#                 children=[
#                     # Row
#                     dcc.Tab(
#                         label="Model Diagnostics",
#                         children= [
#                             html.Div(
#                                 children=[
#                                     html.Div(children=[
#                                         html.Div(
#                                             children=[
#                                                 html.P("Choose a Model to Analyze"),
#                                                 dcc.Dropdown(
#                                                     id='model-choice',
#                                                     options=[{'label': MODEL_NAME, 'value': MODEL_NAME}],
#                                                     value=MODEL_NAME
#                                                     ),
#                                                 html.Div(
#                                                     children=
#                                                     [
#                                                         html.H6(
#                                                             ["Dozer Model Information"], className="subtitle padded"
#                                                             ),
#                                                         html.Table(
#                                                             [
#                                                                 html.Tr(
#                                                                     [
#                                                                         html.Td('Model'),
#                                                                         html.Td(MODEL_NAME)
#                                                                         ]
#                                                                     ),
#                                                                 html.Tr(
#                                                                     [
#                                                                         html.Td('Target Variable'),
#                                                                         html.Td(model[0]['y_var'])
#                                                                         ]
#                                                                     ),
#                                                                 html.Tr(
#                                                                     [
#                                                                         html.Td('Total Number of Data Points'),
#                                                                         html.Td(model[0]['num_data_points'])
#                                                                         ]
#                                                                     ),
#                                                                 html.Tr(
#                                                                     [
#                                                                         html.Td('Number of "True" Data Points'),
#                                                                         html.Td(model[0]['num_true_data_points'])
#                                                                         ]
#                                                                     ),
#                                                                 html.Tr([
#                                                                     html.Td('ROC Score'),
#                                                                     html.Td('%0.3f' % pd.DataFrame(model[0]['metrics'])['test_roc_auc_score'].mean())
#                                                                     ])
#                                                                 ]
# 
#                                                             ),
#                                                         ],
#                                                     className="row",
#                                                     ),
#                                                 ],
#                                             className="two columns"
#                                             ),
#                                         html.Div(
#                                                 id="model-tab",
#                                                 className="ten columns"
#                                                 )],
#                                         className="row")
#                                     ],
#                                 className="row")
#                             ]
#                         ),
#                     dcc.Tab(
#                             label="Investigations",
#                             className="customtab",
# 
#                             # Row 2
#                             # New Row
#                             children=[
#                                 html.Div(
#                                     [
#                                         html.H6(
#                                             ['Model Risk Distribution'],
#                                             className="subtitle padded",
#                                             ),
#                                         html.P("Model: %s" % MODEL_NAME),
#                                         html.P('''
#                                     This graph shows the distribution of predicted models
#                                     '''),
#                                         dcc.Graph(
# 
#                                             figure=fig,
# 
#                                             ),
#                                         # # html.Table(dash_table.DataTable(id='accounts', df_accounts)),
#                                         # html.Table(dash_table.DataTable(
#                                         # id="mytable",
#                                         # columns=[{"name": i, "id": i} for i in df_features[account_cols].columns],
#                                         # page_size=10,
#                                         # data=df_features[account_cols].to_dict('records'),
#                                         # style_cell_conditional=[
#                                         # {
#                                         # 'if': {'column_id': c},
#                                         # 'textAlign': 'left'
#                                         # } for c in ['Date', 'Region']
#                                         # ],
#                                         # style_data_conditional=[
#                                         # {
#                                         # 'if': {'row_index': 'odd'},
#                                         # 'backgroundColor': 'rgb(250, 250, 250)'
#                                         # }
#                                         # ],
#                                         # style_header=table_header_style
#                                         # ))
#                                         ],
#                                     className="row",
#                                     ),
#                                 html.Div(
#                                     [
#                                         html.H6(
#                                             ["Account List"],
#                                             className="subtitle padded",
#                                             ),
#                                         html.P('Click on an account to see prediction details and transactions for the account'),
#                                         # # html.Table(dash_table.DataTable(id='accounts', df_accounts)),
#                                         dash_table.DataTable(
#                                             id="mytable",
#                                             columns=[{"name": i, "id": i, 'type': COL_TYPE_MAP[str(df_features_for_predictions[i].dtype)], 'format': {'specifier': '.3f'}} for i in df_features_for_predictions[account_cols].columns],
#                                             page_size=10,
#                                             data=df_features_for_predictions[account_cols + ['id']].to_dict('records'),
#                                             style_cell_conditional=[
#                                                 {
#                                                     'if': {'column_id': c},
#                                                     'textAlign': 'left'
#                                                     } for c in ['Date', 'Region']
#                                                 ],
#                                             style_data_conditional=[
#                                                 {
#                                                     'if': {'row_index': 'odd'},
#                                                     'backgroundColor': 'rgb(250, 250, 250)'
#                                                     }
#                                                 ],
#                                             style_header=table_header_style,
#                                             style_cell=table_cell_style
#                                             )
# 
#                                         ],
#                                     className="row ",
#                                     ),
#                                 # # Row 3
#                                 html.Div(
#                                         id="transaction-table",
#                                         children = [],
#                                         className="row ",
#                                         ),
#                                 ],
#                             # className="sub_page",
#                             ),
#         ],
#         # className="page",
#     )])
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0')
