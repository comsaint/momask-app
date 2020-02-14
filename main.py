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
from settings import GS_DFFULL_URL
import json
import functools

mapbox_access_token = 'pk.eyJ1IjoiY29tc2FpbnQiLCJhIjoiY2s2Ynpvd2VhMTNlcTNlcGtqamJjb2o3bSJ9.3_uGJ8EBdgxqntrEslskCQ'
bold = {'font-weight': 'bold'}
type_color_map = {'pharmacy': '#0000ff',
                  'organization': '#088A08',
                  'health centre': '#FF8000',
                  'low_supply': '#FF0000'}
low_stock_threshold = 500

dash_app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
                                          {"name": "description",
                                           "content":
                                               "Momask is a real-time, interactive dashbaord visualizing the stock"
                                               " of surgical masks in Macao SAR. The data is supplied by the Macao"
                                               " Health Bureau during the coronavirus outbreak in 2020."},
                                          ])
dash_app.title = "Momask - Macao's Mask Stock"
app = dash_app.server


# precessing of data goes here (generate hovertext, color etc.)
def final_processing(dff):
    """
    # final touch on data before plotting. Note this method is meant for `df_full.csv`
    :param dff:
    :return:
    """
    # 1. Set color
    dff['color'] = dff['poi_type'].map(type_color_map)
    # set red alert color for low inventory
    dff.loc[dff['tolqty_diff'] <= low_stock_threshold, 'color'] = type_color_map['low_supply']

    # 2. Set hover text
    dff['hov_txt'] = '名稱: ' + dff['name'] + '(' + dff['poi_type'] + ')' + '<br>' + \
                     '地址: ' + dff['address'] + '<br>' + \
                     '現時口罩數量: ' + dff['tolqty_diff'].astype(int).astype(str) + '<br>' \
                                                                               '最後更新時間: ' + dff[
                         'human_parsed_timestamp'].apply(
        lambda x: x.strftime('%Y{0}%m{1}%d{2} %H{3}%M{4}').format(*'年月日時分'))

    # 3. get stock by POI and date
    # sort by timestamp
    dff.sort_values('human_parsed_timestamp', ascending=False, inplace=True)
    # new date column
    dff['human_parsed_date'] = dff['human_parsed_timestamp'].dt.date
    # keep most updated entry per date of each code
    df_by_poi_dt = dff.drop_duplicates(subset=['code', 'human_parsed_date'], keep='first')

    # 4. get most updated data
    df_recent = dff.groupby('code').first().reset_index()
    return df_recent, df_by_poi_dt


# modify default template to serve GA's JS in header
# check "Customizing Dash's HTML Index Template" section on https://dash.plot.ly/external-resources
dash_app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Momask - Macao's Mask Stock</title>
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
        <script async type="text/javascript" src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-5e4525db8adc17a7"></script>
    </body>
</html>
'''


# layout in a function for live update.
# See https://dash.plot.ly/live-updates - 'Update on Page Load' section
def serve_layout():
    return html.Div(
                    children=[
                        html.Div(id='intermediate-value', children=[], hidden=True),
                        # update data every 5 minutes. Interval in millisecond
                        dcc.Interval(id='interval-component', interval=1000 * 60 * 5),
                        html.Div(
                            className="row",
                            children=[
                                # Column for user controls
                                html.Div(
                                    className="three columns",
                                    children=[
                                        # html.Img(className="logo", src=app.get_asset_url("dash-logo-new.png")),
                                        html.H1("Momask - 邊度有口罩?"),
                                        html.Div(className="text-padding",
                                                 children=["請點擊口罩購買位置,以獲取更多資訊", ],
                                                 ),
                                        # Map legend
                                        html.Ul(className='style_legend',
                                                children=[
                                                    html.Li("藥房", className='circle',
                                                                    style={'background': type_color_map['pharmacy'], }
                                                            ),
                                                    html.Li("衛生中心", className='circle',
                                                            style={'background': type_color_map['health centre']}
                                                            ),
                                                    html.Li("機構", className='circle',
                                                            style={'background': type_color_map['organization']}
                                                            ),
                                                    html.Li("低庫存(少於{}個)".format(low_stock_threshold),
                                                            className='circle',
                                                            style={'background': type_color_map['low_supply']}
                                                            ),
                                                    ],
                                                ),
                                        html.Br(),
                                        # Information
                                        html.H2(['口罩庫存:'], style=bold),
                                        html.Pre(id='info', children=[], className='style_info_box'),
                                        # useful links
                                        html.Br(),
                                        dcc.Markdown(
                                            children=[
                                                "資料來源:\n[衛生局抗疫專頁](https://www.ssm.gov.mo/apps1/PreventWuhanInfection/ch.aspx)\n",
                                                '\n',
                                                "相關連結:\n[武漢肺炎民間資訊(香港)](https://wars.vote4.hk/)\n",
                                                "有意見/問題? [聯絡我們](mailto:momaskmacao@gmail.com)\n"
                                            ]
                                        ),
                                        html.Br(),
                                        # social share
                                        html.Div(className='addthis_inline_share_toolbox_m4ht', ),
                                        html.Br(),
                                        # disclaimer
                                        html.Div(children=[
                                            html.P('免責聲明', style={"text-align": "center"}),
                                            html.P(className='disclaimer', children=[
                                                "本網頁所載的所有資料謹供參考之用。Admin只能盡力確保準確性，"
                                                "但不會對任何錯誤或遺漏承擔責任。如有任何疑問，請以官方公佈資料為準。"
                                            ]),
                                        ]),
                                    ],
                                ),
                                # Column for app graphs and plots
                                html.Div(
                                    className="eight columns div-for-charts",
                                    children=[
                                        dcc.Loading(id="loading-icon1", type="default", children=[
                                            dcc.Graph(id="map-graph"),]),
                                        dcc.Loading(id="loading-icon2", type="default", children=[
                                            dcc.Graph(id="bar-chart"),]),
                                    ],
                                ),
                            ],
                        ),
                    ],
    )


dash_app.layout = serve_layout()


# function to draw the map
def draw_map(df):
    # Create figure
    locations = [go.Scattermapbox(
        lon=df['x'],
        lat=df['y'],
        text=df['name'],
        textfont=dict(family='NSimSun serif',
                      size=30,
                      color='#000'
                      ),
        mode='markers+text',
        marker={'color': df['color'],
                'opacity': 0.5,
                'size': df['tolqty_diff'],
                'sizeref': 30,
                'sizemin': 10,
                'sizemode': 'area'
                },
        unselected={'marker': {'opacity': 0.5}},
        selected={'marker': {'opacity': 1}},
        hoverinfo='text',
        hovertext=df['hov_txt'],
        customdata=df['human_parsed_timestamp']
    )]
    # Return figure
    return {
        'data': locations,
        'layout': go.Layout(
            autosize=True,
            uirevision='foo',  # preserves state of figure/map after callback activated
            margin=go.layout.Margin(l=0, r=35, t=0, b=0),
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                style='streets',
                center=dict(
                    lat=22.198818,
                    lon=113.545521
                ),
                pitch=0,
                zoom=13,
            ),
        )
    }


# function to draw the bar chart
def draw_bar_chart(df):
    df = df.groupby('human_parsed_date').agg({'tolqty_diff': sum})
    data = go.Bar(x=df.index, y=df['tolqty_diff'], opacity=0.8,
                  text=df['tolqty_diff'], texttemplate='%{y:,}個', textposition='auto',
                  hovertemplate='%{x}:%{y:,}個', hoverinfo="y",)
    return {
        'data': [data, ],
        'layout': go.Layout(
            title='口罩庫存',
            autosize=True,
            uirevision='foo2',  # preserves state of figure/map after callback activated
            clickmode='event+select',
            xaxis={'title': '日期'},
            yaxis={'title': '口罩庫存(個)'},
            font=dict(
                family="Courier New, monospace",
                size=18,
                color="#7f7f7f"
            )
        )
    }


@dash_app.callback(
    Output('info', 'children'),
    [Input('map-graph', 'clickData')])
def display_click_poi_info(clickData):
    if clickData is None:
        return ''
    else:
        infos = clickData['points'][0]['hovertext'].replace('<br>', '\n')
        return infos


# graphs update
@dash_app.callback(Output('map-graph', 'figure'),
                   [Input('intermediate-value', 'children')])
def update_map(jsonified_cleaned_data):
    datasets = json.loads(jsonified_cleaned_data)
    df = pd.read_json(datasets['df_most_update'], orient='split')
    return draw_map(df)


@dash_app.callback(Output('bar-chart', 'figure'),
                   [Input('intermediate-value', 'children'),])
def update_bar_chart(jsonified_cleaned_data):
    datasets = json.loads(jsonified_cleaned_data)
    df = pd.read_json(datasets['df_by_day'], orient='split')
    return draw_bar_chart(df)


# for live-updating data at every `n_intervals`
@dash_app.callback(
    Output('intermediate-value', 'children'),
    [Input('interval-component', 'n_intervals')])
@functools.lru_cache(maxsize=32)
def clean_data(n):
    df = pd.read_csv(GS_DFFULL_URL, encoding='utf-8',
                     parse_dates=['parsed_timestamp', 'human_parsed_timestamp'],
                     infer_datetime_format=True,
                     low_memory=False)
    print(df['human_parsed_timestamp'].max())
    df_most_update, df_by_day = final_processing(df)
    datasets = {
         'df_most_update': df_most_update.to_json(orient='split', date_format='iso'),
         'df_by_day': df_by_day.to_json(orient='split', date_format='iso'),
    }
    return json.dumps(datasets)
# --------------------------------------------------------------


@app.after_request
def set_response_headers(response):
    response.headers['Cache-Control'] = 'private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '300'
    return response


if __name__ == '__main__':
    dash_app.run_server(debug=False)
