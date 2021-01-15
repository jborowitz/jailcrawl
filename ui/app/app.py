# -*- coding: utf-8 -*-
import dash_tabulator
import dash_bootstrap_components as dbc
import dash_table
import datetime
import glob
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pathlib
import plotly.graph_objs as go
import json
import plotly.express as px
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
import boto3
s3 = boto3.client(
        "s3",
        region_name='us-east-1'
        )
# print([b.name for b in s3.buckets.all()])
countypop = pd.read_csv('/app/assets/countypop.csv')
state_name_to_code = {'Alabama':'AL',
'Alaska':'AK',
'Arizona':'AZ',
'Arkansas':'AR',
'California':'CA',
'Colorado':'CO',
'Connecticut':'CT',
'Delaware':'DE',
'Florida':'FL',
'Georgia':'GA',
'Hawaii':'HI',
'Idaho':'ID',
'Illinois':'IL',
'Indiana':'IN',
'Iowa':'IA',
'Kansas':'KS',
'Kentucky':'KY',
'Louisiana':'LA',
'Maine':'ME',
'Maryland':'MD',
'Massachusetts':'MA',
'Michigan':'MI',
'Minnesota':'MN',
'Mississippi':'MS',
'Missouri':'MO',
'Montana':'MT',
'Nebraska':'NE',
'Nevada':'NV',
'New Hampshire':'NH',
'New Jersey':'NJ',
'New Mexico':'NM',
'New York':'NY',
'North Carolina':'NC',
'North Dakota':'ND',
'Ohio':'OH',
'Oklahoma':'OK',
'Oregon':'OR',
'Pennsylvania':'PA',
'Rhode Island':'RI',
'South Carolina':'SC',
'South Dakota':'SD',
'Tennessee':'TN',
'Texas':'TX',
'Utah':'UT',
'Vermont':'VT',
'Virginia':'VA',
'Washington':'WA',
'West Virginia':'WV',
'Wisconsin':'WI',
'Wyoming':'WY'}

# 3rd party js to export as xlsx
external_scripts = ['https://oss.sheetjs.com/sheetjs/xlsx.full.min.js']

# bootstrap css
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css']

app = dash.Dash(
        __name__,
        meta_tags=[{"name": "viewport", "content": "width=device-width"}],
        suppress_callback_exceptions=True,
        external_scripts=external_scripts, external_stylesheets=external_stylesheets
        )

# columns = [
        # { "title": "County", "field": "County", "width": 150, "headerFilter":True},
        # { "title": "State", "field": "State", "headerFilter": True},
        # { "title": "Date", "field": "Date", "headerFilter":True },
        # { "title": "Link", "field": "Link"},
        # ]
columns = [
        { "name": "County", "id": "County"},
        { "name": "State", "id": "State"},
        { "name": "Date", "id": "Date"},
        { "name": "Link", "id": "Link", 'type':'text','presentation':'markdown'},
        ]
downloadButtonType = {"css": "btn btn-primary", "text":"Export", "type":"xlsx"}
clearFilterButtonType = {"css": "btn btn-outline-dark", "text":"Clear Filters"}

BUCKET_NAME='jailcrawl'
def get_exit_codes():
    bucket = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="daily_run_summaries/%s" % datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m'))
    bucket['Contents'].sort(key = lambda x: x['Key'])
    key = bucket['Contents'][-1]
    obj = s3.get_object(Bucket='jailcrawl', Key=key['Key'])
    print('Latest run summary is _%s_' % key['Key'])
    exit_codes = pd.read_csv(obj['Body'])
    return exit_codes


def get_page_counts():
    bucket = s3.list_objects_v2(Bucket='jailcrawl', Prefix="page_counts/%s" % datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m'))
    bucket['Contents'].sort(key = lambda x: x['Key'])
    key = bucket['Contents'][-1]
    obj = s3.get_object(Bucket='jailcrawl', Key=key['Key'])
    print('Latest page counts is _%s_' % key['Key'])
    page_counts = pd.read_csv(obj['Body'])
    return page_counts

def load_all_run_summaries():
    out_list = []
    for f in glob.glob('daily_run_summaries/*.csv'):
        df = pd.read_csv(f)
        date_str = f.split('/')[1].split('-run')[0]  
        df['date'] = date_str
        df['filename'] = f.split('/')[1]
        out_list.append(df)
    df = pd.concat(out_list)
    del out_list
    return df

def get_state_from_script(scriptname):
    words = scriptname.replace('.py','').split('_')
    if words[0] == 'Hawai':
        return 'Hawaii'
    if words[0] in state_name_to_code.keys():
        return words[0]
    else:
        if ' '.join(words[0:2]) in state_name_to_code.keys():
            return' '.join(words[0:2])
        else:
            print(words)
def get_county_from_script(scriptname):
    words = scriptname.replace('.py','').split('_')
    if words[0] == 'Hawai':
        return words[1]
    if words[0] in state_name_to_code.keys():
        return ' '.join(words[1:])
    else:
        if ' '.join(words[0:2]) in state_name_to_code.keys():
            return ' '.join(words[2:])
        else:
            print(words)

countypop['fips_str'] = countypop['fips'].apply(lambda x: '%05.0f' % x)
countypop['fips_state'] = countypop['fips_str'].apply(lambda x: x[0:2])  
state_fips_to_code = {v['fips_state']:v['abbr'] for k, v in countypop.drop_duplicates(['fips_state','abbr'])[['fips_state','abbr']].iterrows()}
def add_fips_to_run_summaries(df, how='all_states'):
    df['county'] = df['script'].apply(lambda x: x.split('_')[1].replace('.py',''))
    df['state'] = df['script'].apply(get_state_from_script)
    df['county_match'] = df['script'].apply(get_county_from_script)
    df['state_code'] = df['state'].apply(lambda x: state_name_to_code[x])
    countypop['cn'] = countypop['county'].apply(lambda x: x.replace('County','').lower().strip())                          
    me = df.merge(countypop, left_on=['state_code','county_match'], right_on=['abbr','cn'], how='left')
    print(me[me['fips'].isnull()]['script'].unique())
    me = df.merge(countypop, left_on=['state_code','county_match'], right_on=['abbr','cn'])
    if how=='all_states':
        me = me.drop_duplicates('fips')
    elif how=='all_dates':
        me = me[['date','fips','exit_code']]
    me['fips'] = me['fips'].apply(lambda x: '%05.0f' % x) 
    me['ones'] = True
    return me

counties = json.load(open('/app/assets/geojson-counties-fips.json'))
counties_df = pd.DataFrame(counties['features'])
counties_df['fips_state'] = counties_df['id'].apply(lambda x: x[0:2])
counties_df['state_code_all'] = counties_df['fips_state'].apply(lambda x: state_fips_to_code.get(x, ''))
codes = load_all_run_summaries()
df = add_fips_to_run_summaries(codes)
me = counties_df[['properties','id','state_code_all']].merge(df, left_on='id', right_on='fips', how='left')
me['county_from_geojson'] = me['properties'].apply(lambda x: x['NAME'])
me['name'] = me.apply(lambda x: '%s, %s' % (x['county_from_geojson'],x['state_code_all']), axis=1)
me['ones'] = me['ones'].fillna(False)
# page_counts = get_page_counts()

fig = px.choropleth(me, geojson=counties, locations='id', color='ones',
        # color_continuous_scale="Viridis",
        # range_color=(0, 12),
        title="Jail Crawl County Coverage",
        hover_name='name',
        hover_data={i:False for i in me.columns if i != 'ones'},
        scope="usa",
        labels={'ones':'Crawled'}
        )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

df2 = add_fips_to_run_summaries(codes, how='all_dates')
df2 =df2.drop_duplicates(['date','fips'])
counts = pd.DataFrame(df2[df2['exit_code'] == 0].groupby('date').size().sort_index()).reset_index()
print(counts.head())
fig2 = px.line(counts, x='date', y=0, title='Crawled Counties over Time')

app.layout = dbc.Container(
        [
            html.H2("CGU Computational Justice Lab Jail Crawl Data"),
            dbc.Row(
                [
                dbc.Col([
                    dcc.Graph(
                        id='graph',
                        figure=fig
                        ),
                    html.P("This map shows counties for which a crawl successfully completed as of %s. Click a county to see a list raw stored sites." % codes['date'].max())
                    ], md=12),
                ]
                ),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id='counts',
                        figure=fig2
                        ),
                    html.P("This graph shows the number of successfully crawled county jail websites per day. Large dropoffs indicate missing data. Daily fluctuations are due to automated bot detection systems that do not work deterministically and result in some blocks and some results.")],
                    md=6),
                dbc.Col([
                    html.Div(id='tabulator')
                    ],
                    md=6)
                ])
            # html.P(
                # id='click-data'
                # ),
            ]
            )
@app.callback(
    Output('tabulator', 'children'),
    Input('graph', 'clickData'))
def display_click_data(clickData):
    print(clickData)
    # df2[df2['fips'] == clickData['points'][0]['location']]
    if clickData is None:
        return None
    try:
        row = me[me['fips'] == clickData['points'][0]['location']].iloc[0]
    except IndexError:
        print('No crawls for county %s' % clickData)
        return None

    script = row['script']
    state = get_state_from_script(script)
    county = get_county_from_script(script)
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket='jailcrawl', Prefix="%s/%s/" % (state, county))
    page_link_list  = []
    page_link_name  = []
    for page in pages:
        for obj in page['Contents']:
            page_link_list.append('[%s](https://%s.s3.%s.amazonaws.com/%s)' % (obj['Key'],BUCKET_NAME, 'us-east-1',obj['Key'] ))
            # page_link_list.append('<a href="https://%s.s3.%s.amazonaws.com/%s">%s</a>' % (BUCKET_NAME, 'us-east-1',obj['Key'], obj['Key']))
            # page_link_list.append(html.A(html.P(obj['Key']),href='https://%s.s3.%s.amazonaws.com/%s' % (BUCKET_NAME, 'us-east-1',obj['Key'])))
            page_link_name.append(obj['Key'])
    page_df = pd.DataFrame({'Link': page_link_name, 'Link Name': page_link_name})
    page_df['State'] = state
    page_df['County'] = county
    page_df['Date'] = page_df['Link Name'].apply(lambda x: x.split('/')[4].split(' ')[0])
    data = page_df.to_dict(orient='records')
    # bucket = s3.list_objects_v2(Bucket='jailcrawl', Prefix="%s/%s/" % (state, county))
    tabulator = dash_table.DataTable(
        columns=columns,
        data=data,
        page_size=10,
        export_format="csv",
        # theme='tabulator_simple',
        # options=options,
        # downloadButtonType=downloadButtonType,
        # clearFilterButtonType=clearFilterButtonType
        )
    return [
            html.P("This table lists all available files for the selected location. For access to these files, please contact the Computational Justice Lab."),
            tabulator,
            ]
if __name__ == "__main__":
    app.run_server( host='0.0.0.0')
