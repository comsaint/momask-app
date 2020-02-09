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
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from update_data import update_data
from settings import ASSETS_FOLDER

mapbox_access_token = 'pk.eyJ1IjoiY29tc2FpbnQiLCJhIjoiY2s2Ynpvd2VhMTNlcTNlcGtqamJjb2o3bSJ9.3_uGJ8EBdgxqntrEslskCQ'
blackbold = {'color': 'black', 'font-weight': 'bold'}

dash_app = dash.Dash(__name__)
app = dash_app.server

sched = BackgroundScheduler(daemon=True)
sched.add_job(update_data, 'interval', minutes=15)
sched.start()
atexit.register(lambda: sched.shutdown(wait=False))

# modify default template to serve GA's JS in header
# Check "Customizing Dash's HTML Index Template" section on https://dash.plot.ly/external-resources
dash_app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>mask stock in Macao</title>
        <meta name="description=" 
        content="Momask is a real-time, interactive dashbaord visualizing the stock of surgical masks in Macao SAR. 
        The data is supplied by the Macao Health Bureau during the coronavirus outbreak in 2020.">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {%favicon%}
        {%css%}
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-157950932-1"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'UA-157950932-1');
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
        <div>Disclaimer:</div>
    </body>
</html>
'''

# final touch on data
# read data
df = pd.read_csv(ASSETS_FOLDER / 'df.csv',
                 encoding='utf-8',
                 parse_dates=['human_parsed_timestamp'],
                 infer_datetime_format=True)
# get latest update time
latest_time = df['human_parsed_timestamp'].max()
# set color
df.loc[df['tolqty_diff'] <= 1000, 'color'] = '#a9a9a9'  # grey
df.loc[df['tolqty_diff'] <= 100, 'color'] = '#000000'  # black

# layout of app
dash_app.layout = html.Div(children=[
    html.Div([
        html.Div([
            # Map-legend
            html.Ul([
                html.Li("藥房", className='circle', style={'background': '#0000ff', 'color': 'black',
                                                         'list-style': 'none', 'text-indent': '17px',
                                                         'white-space': 'nowrap'}),
                html.Li("衛生中心", className='circle', style={'background': '#FF0000', 'color': 'black',
                                                           'list-style': 'none', 'text-indent': '17px',
                                                           'white-space': 'nowrap'}),
                html.Li("機構", className='circle', style={'background': '#824100', 'color': 'black',
                                                         'list-style': 'none', 'text-indent': '17px',
                                                         'white-space': 'nowrap'}),
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
            html.Br(),
            html.P("點擊口罩購買位置,獲取更多資訊"),

            # Web_link
            html.Label(['參考來源:'], style=blackbold),
            html.Pre(id='web_link', children=[],
                     style={'white-space': 'pre-wrap', 'word-break': 'break-all',
                            'border': '1px solid black', 'text-align': 'center',
                            'padding': '12px 12px 12px 12px', 'color': 'blue',
                            'margin-top': '3px'}
                     ),

            # Information
            html.Br(),
            html.Label(['口罩庫存:'], style=blackbold),
            html.Pre(id='info', children=[],
                     style={'white-space': 'pre-wrap', 'word-break': 'break-all',
                            'border': '1px solid black', 'text-align': 'left',
                            'padding': '12px 12px 12px 12px', 'color': 'black',
                            'margin-top': '3px'}
                     ),

            # Noted
            html.Br(),
            html.Label(['最後更新時間:'], style=blackbold),
            html.Pre(id='noted', children=[latest_time],
                     style={'white-space': 'pre-wrap', 'word-break': 'break-all',
                            'border': '1px solid black', 'text-align': 'center',
                            'padding': '12px 12px 12px 12px', 'color': 'blue',
                            'margin-top': '3px'}
                     ),

            # useful links
            html.Br(),
            html.Label(['相關連結:'], style=blackbold),
            html.Pre(id='links', children=[
                html.A("衛生局抗疫專頁",
                       href="https://www.ssm.gov.mo/apps1/PreventWuhanInfection/ch.aspx",
                       target="_blank"),
                html.Br(),
                html.A("武漢肺炎民間資訊(香港)",
                       href="https://wars.vote4.hk/",
                       target="_blank"),
            ]),
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
    locations = [go.Scattermapbox(
        lon=df_sub['longitude'],
        lat=df_sub['latitude'],
        text=df_sub['name_location'],
        textfont=dict(family='NSimSun serif',
                      size=30,
                      color='#000'
                      ),
        mode='markers+text',
        marker={'color': df_sub['color'],
                'opacity': 0.5,
                'size': df_sub['tolqty_diff'],
                'sizeref': 30,
                'sizemin': 10,
                'sizemode': 'area'
                },
        unselected={'marker': {'opacity': 0.5}},
        selected={'marker': {'opacity': 1, 'color': '#00ff00'}},
        hoverinfo='text',
        hovertext=df_sub['hov_txt'],
        customdata=df_sub['website']
    )]
    # Return figure
    return {
        'data': locations,
        'layout': go.Layout(
            uirevision='foo',  # preserves state of figure/map after callback activated
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            title=dict(text="邊度有口罩?", font=dict(size=50, color='green')),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                style='streets',
                center=dict(
                    lat=22.19392,
                    lon=113.54371
                ),
                pitch=0,
                zoom=13.5,
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
        return ''
    else:
        the_link = clickData['points'][0]['customdata']
        if the_link is None:
            return 'No Website Available'
        else:
            return html.A(the_link, href=the_link, target="_blank")


@dash_app.callback(
    Output('info', 'children'),
    [Input('graph', 'clickData')])
def display_click_poi_info(clickData):
    if clickData is None:
        return ''
    else:
        infos = clickData['points'][0]['hovertext'].replace('<br>', '\n')
        return infos


# --------------------------------------------------------------


if __name__ == '__main__':
    dash_app.run_server()
