#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

mapbox_access_token = 'pk.eyJ1IjoiY29tc2FpbnQiLCJhIjoiY2s2Ynpvd2VhMTNlcTNlcGtqamJjb2o3bSJ9.3_uGJ8EBdgxqntrEslskCQ'
blackbold = {'color': 'black', 'font-weight': 'bold'}

dash_app = dash.Dash(__name__)
app = dash_app.server

# read data
df = pd.read_csv('https://storage.googleapis.com/momask/df.csv',
                 encoding='utf-8',
                 parse_dates=['human_parsed_timestamp'],
                 infer_datetime_format=True)
latest_time = df['human_parsed_timestamp'].max()

dash_app.layout = html.Div(children=[
    html.Div([
        html.Div([
            # Map-legend
            html.Ul([
                html.Li("Pharmacy", className='circle', style={'background': '#0000ff', 'color': 'black',
                                                               'list-style': 'none', 'text-indent': '17px',
                                                               'white-space': 'nowrap'}),
                html.Li("HealthCenter", className='circle', style={'background': '#FF0000', 'color': 'black',
                                                                   'list-style': 'none', 'text-indent': '17px'}),
                html.Li("Organisation", className='circle', style={'background': '#824100', 'color': 'black',
                                                                   'list-style': 'none', 'text-indent': '17px'}),
            ], style={'border-bottom': 'solid 3px', 'border-color': '#00FC87', 'padding-top': '6px'}
            ),

            # Borough_checklist
            html.Label(children=['Display: '], style=blackbold),
            dcc.Checklist(id='boro_name',
                          options=[{'label': str(b), 'value': b} for b in sorted(df['boro'].unique())],
                          value=[b for b in sorted(df['boro'].unique())],
                          ),

            # Recycling_type_checklist
            html.Label(children=['Looking for masks: '], style=blackbold),
            dcc.Checklist(id='recycling_type',
                          options=[{'label': str(b), 'value': b} for b in sorted(df['type'].unique())],
                          value=[b for b in sorted(df['type'].unique())],
                          ),

            # Web_link
            html.Br(),
            html.Label(['Sources:'], style=blackbold),
            html.Pre(id='web_link', children=[],
                     style={'white-space': 'pre-wrap', 'word-break': 'break-all',
                            'border': '1px solid black', 'text-align': 'center',
                            'padding': '12px 12px 12px 12px', 'color': 'blue',
                            'margin-top': '3px'}
                     ),

            # Noted
            html.Br(),
            html.Label(['Last Updated Time:'], style=blackbold),
            html.Pre(id='noted', children=[latest_time],
                     style={'white-space': 'pre-wrap', 'word-break': 'break-all',
                            'border': '1px solid black', 'text-align': 'center',
                            'padding': '12px 12px 12px 12px', 'color': 'blue',
                            'margin-top': '3px'}
                     ),

        ], className='three columns'
        ),

        # Map
        html.Div([
            dcc.Graph(id='graph', config={'displayModeBar': False, 'scrollZoom': True},
                      style={'background': '#00FC87', 'padding-bottom': '2px', 'padding-left': '2px', 'height': '100vh'}
                      )
        ], className='nine columns'
        ),

    ], className='row'
    ),
])


@dash_app.callback(Output('graph', 'figure'),
                   [Input('boro_name', 'value'),
                    Input('recycling_type', 'value')])
def update_figure(chosen_boro, chosen_recycling):
    df_sub = df[(df['boro'].isin(chosen_boro)) &
                (df['type'].isin(chosen_recycling))]

    # Create figure
    locations=[go.Scattermapbox(
                    lon=df_sub['longitude'],
                    lat=df_sub['latitude'],
                    mode='markers',
                    marker={'color': df_sub['color']},
                    unselected={'marker': {'opacity': 1}},
                    selected={'marker': {'opacity': 0.5, 'size': 25}},
                    hoverinfo='text',
                    hovertext=df_sub['hov_txt'],
                    customdata=df_sub['website']
    )]
    # Return figure
    return {
        'data': locations,
        'layout': go.Layout(
            uirevision='foo', # preserves state of figure/map after callback activated
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            title=dict(text="邊度搵口罩?",font=dict(size=50, color='green')),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=25,
                style='light',
                center=dict(
                    lat=22.156760,
                    lon=113.558500
                ),
                pitch=40,
                zoom=13.5
            ),
        )
    }
# ---------------------------------------------------------------
# callback for Web_link


@dash_app.callback(
    Output('web_link', 'children'),
    [Input('graph', 'clickData')])
def display_click_data(clickData):
    if clickData is None:
        return '點擊想購買口罩的位置,以獲取更多資訊'
    else:
        # print (clickData)
        the_link=clickData['points'][0]['customdata']
        if the_link is None:
            return 'No Website Available'
        else:
            return html.A(the_link, href=the_link, target="_blank")
# --------------------------------------------------------------


if __name__ == '__main__':
    dash_app.run_server(debug=True)
