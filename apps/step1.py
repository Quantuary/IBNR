#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 12 11:42:17 2021

@author: mleong
"""

#import os
#os.chdir(r"R:\Technical\04 Actuarial Pricing\Technical Analytics\travel\notebooks\Marcus's")
#os.chdir(r"/home/marcus/Documents/git/IBNR")

import datetime
from app import app, IBNR, MyPickle, html, dcc, dbc, dash, dash_table, Format, Scheme, Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# generate IBNR methods options
IBNR_method_options = [{'label':key, 'value':key} for key in IBNR.model_params]

def handle_blank(x):
    if not x:
        x =  None
    else:
        x
    return x

def edit_params(ibnr_methods, drop_valuation, drop_coordinate):
    params = IBNR.model_params[ibnr_methods]
    
    # Drop valuation month
    if drop_valuation != None:
        params['drop_valuation'] =  drop_valuation.split(";")
    else:
        params['drop_valuation'] =  None
    
    # specific cell
    if drop_coordinate != None:
        elements = drop_coordinate.split(";")
        drop_list = []
        for i in range(len(elements)):
            x = elements[i].split(",")[0]
            y = eval(elements[i].split(",")[1])
            
            drop_list.append((x,y))
            params['drop'] =drop_list
    else:
        params['drop'] =  None
    return params
    
def discrete_background_color_bins(df, n_bins=5, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    #df_min = df_numeric_columns.min().min()
    df_min = 0 #avoid formating negative numbers
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    #legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Reds'][i - 1] 
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} > {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })

# =============================================================================
#         legend.append(
#             html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
#                 html.Div(
#                     style={
#                         'backgroundColor': backgroundColor,
#                         'borderLeft': '1px rgb(50, 50, 50) solid',
#                         'height': '10px'
#                     }
#                 ),
#                 html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
#             ])
#         )
#     return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))
# =============================================================================
    return styles

NAV_STYLE = {
            "height": 10,
            "padding": "2rem 1rem",
            }
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 50,
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}
CONTENT_STYLE = {
    "margin-left": "20rem",
    "padding": "5rem 1rem",
}
FOOTER_STYLE = {
    #"position": "fixed",
    "bottom": 0,
    "right": 0,
    #"margin-left": "22rem",
    "height": 30,
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# HTML component
select_product_code_claim = html.Div([
                                     html.P('Product Claim Code:', className='thick underline'),
                                     dcc.Dropdown(
                                        id='product_code_claim',
                                        options=[{'label':'111', 'value':'111'},
                                                 {'label':'116', 'value':'116'},
                                                 {'label':'119', 'value':'119'},
                                                 {'label':'126', 'value':'126'},
                                                 {'label':'430', 'value':'430'},
                                                 {'label':'431', 'value':'431'},
                                                 {'label':'432', 'value':'432'},
                                                 {'label':'441', 'value':'441'},
                                                 {'label':'442', 'value':'442'},
                                            ],
                                        value=['119'],
                                        multi=True,
                                        persistence=True, persistence_type='memory'
                                            )
                                     ])
select_risk_cluster = html.Div([
                                html.P('Risk Cluster:', className='thick underline'),
                                dcc.Dropdown(
                                   id='risk_group',
                                   #value=None,
                                   multi=True,
                                   persistence=True, persistence_type='memory'
                                       )
                                ])
select_lookback = html.Div([
                            dcc.Slider(
                                id = 'lookback_period',
                                min=1,
                                max=60,
                                step=1,
                                value=13,
                                vertical=True,
                                verticalHeight=150,
                                ),
                            html.P(id='slider_lookback_period')
                            ])
select_development_period = html.Div([
                                    html.P(id='slider_development_period') ,
                                    dcc.Slider(
                                        id = 'development_period',
                                        min=1,
                                        max=60,
                                        step=1,
                                        value=13 )               
                                    ])
select_claim_category = html.Div([
                                html.P('Claim Category:', className='thick underline'),
                                dcc.Checklist(
                                    id = 'claim_category',
                                    options=[
                                        {'label': 'Working Loss', 'value': 'Working Loss'},
                                        {'label': 'Large Loss', 'value': 'Large Loss'},
                                        {'label': 'Event Loss', 'value': 'Event Loss'}],
                                    value=['Working Loss'],
                                    labelStyle={'display': 'inline-block',
                                                "padding-right" : "0.5rem",
                                                },
                                    persistence=True, persistence_type='memory'
                                               )  
                                ])
select_ibnr_method =  html.Div([
                                html.P('IBNR Method:', className='thick'),
                                dcc.Dropdown(
                                    id='ibnr_methods',
                                    options=IBNR_method_options,
                                    value='12m-simple',
                                    multi=False
                                    )   
                                ], className = 'twelve columns' )
select_drop_valuation = html.Div([
                                html.P('Drop Valuation Month:', style={"margin-top": "50px",
                                                                  'font-weight' : 'bold'}),
                                dcc.Input(
                                id='drop_valuation',
                                type='text',
                                debounce=True,
                                value=None,
                                placeholder="yyyy-mm; ",
                                className='col-form-label eleven columns '
                                    )
                                ], className='six columns')
markdown_drop_valuation = html.Div([
                                    html.Div(["Info"],className="card-header"),
                                    html.Div([
                                        dcc.Markdown('''
                                                    *To exclude **more than ONE** valuation month please input as follow: *
                                                     > 
                                                         2020-12; 2020-11
                                                         semicolon as delimiter
                                                     '''
                                                    )
                                        ],className="card-body")
                                    ],className='card border-info mb-3')
card_drop_valuation = html.Div([
                                select_drop_valuation,
                                html.Div([markdown_drop_valuation], className="six columns"),
                                ],className='row')                                    
select_drop_coordinate = html.Div([
                                html.P('Drop Coordinate:', style={"margin-top": "50px",
                                                                  'font-weight' : 'bold'}),
                                dcc.Input(
                                id='drop_coordinate',
                                type='text',
                                debounce=True,
                                value=None,
                                placeholder="yyyy-mm,column_idx; ",
                                className='col-form-label eleven columns'
                                    )
                                ], className='six columns')
markdown_drop_coordinate = html.Div([
                                     html.Div(["Info"],className="card-header thick"),
                                     html.Div([dcc.Markdown('''
                                                            *To exclude **more than ONE** cell please input as follow: *
                                                              > 
                                                                  2020-12,1; 2020-11,2
                                                                  x-cordidate is separated by a comma
                                                              '''
                                                            )
                                               ], className='card-body')
                                     ],className='card border-info mb-3')
card_drop_coordinate = html.Div([
                                select_drop_coordinate,
                                html.Div([markdown_drop_coordinate],className="six columns")
                                ], className='row')             
table_ldf = dash_table.DataTable(
                        id='ldf',
                        columns=None,
                        data=None,
                        export_format="csv",
                        merge_duplicate_headers=True,
                        style_data_conditional = None,
                        style_header={
                            'fontWeight': 'bold',
                            'textAlign': 'center'
                            },
                        style_table={'overflowX': 'auto'},
                                    )
table_cdf = dash_table.DataTable(
                    id='cdf',
                    columns=None,
                    data=None,
                    export_format="csv",
                    style_data_conditional = None,
                    style_header={
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                        },
                    style_table={'overflowX': 'auto'},                    
                                )
table_link_ratio = dash_table.DataTable(
                    id='df',
                    columns=None,
                    data=None,
                    export_format="csv",
                    merge_duplicate_headers=True,
                    style_data_conditional = None,
                    style_header={
                        'fontWeight': 'bold',
                        'textAlign': 'center'
                        },
                    style_table={'overflowX': 'auto'},                    
                                     )
table_log = dash_table.DataTable(
                id = 'params_history',
                columns = [{'name': 'product_code_claim', 'id': 'product_code_claim'},
                            {'name': 'risk_group', 'id': 'risk_group'},
                            {'name': 'claim_category', 'id': 'claim_category'},
                            {'name': 'updated_on', 'id': 'updated_on'},
                            {'name': 'params', 'id': 'params'}
                            ],
                data = None,
                row_selectable="multi",
                selected_rows =[],
                row_deletable=False,
                sort_action="native",
                page_current= 0,
                page_size= 10,
                style_header={'textAlign': 'center'},
                style_table={'overflowX': 'auto'},                  
                )
table_incremental = html.Div([
                            html.H2('Incremental Triangle'),
                            dash_table.DataTable(
                                id='incremental triangle',
                                columns=None,
                                data=None,
                                export_format="csv",
                                merge_duplicate_headers=True,
                                style_data_conditional = None,
                                style_header={
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'
                                    },
                                style_table={'overflowX': 'auto'},
                                )
                            ])
table_cummulative = html.Div([
                            html.H2('Cummulative Triangle'),
                            dash_table.DataTable(
                                id='cummulative triangle',
                                columns=None,
                                data=None,
                                export_format="csv",
                                merge_duplicate_headers=True,
                                style_data_conditional = None,
                                style_header={
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'
                                    },
                                style_table={'overflowX': 'auto'},                                
                                )  
                            ])
table_valuation = html.Div([
                            html.H2('Valuation Triangle'),
                            dash_table.DataTable(
                                id='valuation triangle',
                                columns=None,
                                data=None,
                                export_format="csv",
                                merge_duplicate_headers=True,
                                style_data_conditional = None,
                                style_header={
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'},
                                style_table={
                                    'overflowX': 'auto'},
                                )    
                            ])
graph = dcc.Graph(
                 id="graph",
                 className='row'
                 )
nav = dbc.Nav([ html.H2(children="I.B.N.R.", style={"color":"#fff", "margin-right": "2rem"}),               
                dbc.DropdownMenu(
                    [dbc.DropdownMenuItem(html.A("Incremental", href="#incremental triangle"), className="dropdown-item"),
                     dbc.DropdownMenuItem(html.A("Cumulative", href="#cummulative triangle"), className="dropdown-item"),
                     dbc.DropdownMenuItem(html.A("Valuation", href="#valuation triangle"), className="dropdown-item")],
                    label="Triangles",
                    ),
                dbc.NavLink(html.A("Development Factors", href="#mid")),
                dbc.NavLink(html.A("Saved Parameters", href="#saved_parameters")),
                dbc.NavLink("Step Two ", href="/step_two"),
                ],
                pills=True,
                className="navbar navbar-expand-lg navbar-dark bg-primary fixed-top",       
                style = NAV_STYLE
            )
sidebar = html.Div([
                html.P('''
                IBNR allocation is a framework to allocate quarterly IBNR to monthly IBNR and subsequently 
                into groups of clients or risk cluster.
                '''),
                html.Hr(),
                select_product_code_claim, 
                select_risk_cluster,
                html.P("Select Period:", className='thick underline'),
                html.Div([
                        select_development_period,    
                        select_lookback
                        ], style= {
                            "color": '#0F0F77',
                            "background-color": "#FDF4F6"}),
                html.Div([select_claim_category]),
                ],
            style=SIDEBAR_STYLE,
            )
content = html.Div([
        
       html.Div([
            html.Img(src='/assets/Allianz_Partners_Logo_positive_HEX.png',
                     style={
                            'height': '30%',
                            'width': '30%',
                            'float': 'right',
                            'position': 'relative',
                            'margin-bottom': 10,                             
                         }
                    ),
            ], className='row'),
                
      html.Div([      
            html.Hr(),             
# =============================================================================
#             TRIANGLES
# =============================================================================
            html.Div([
                html.H1('TRIANGLES'),
                table_incremental,
                html.Br(),
                table_cummulative,
                html.Br(),
                table_valuation
                    ]),            
# =============================================================================
#             DEVELOPMENT FACTORS
# =============================================================================         
            html.Hr(),
            html.H1('DEVELOPMENT FACTORS', id='mid'),
            html.Div([
                html.Div([
                        html.Div([select_ibnr_method], className='row'),
                        html.Br(),
                        card_drop_valuation,
                        card_drop_coordinate 
                        ], className='six columns'),
                  
                html.Div([
                          graph,
                          html.Button('SAVED', id='saved', n_clicks=0, className="btn btn-success btn-lg btn-block")
                          ], className='six columns')
                ],className='row'),
            
            
            html.H2('Link Ratio'),
            table_link_ratio,
            html.Br(),
            
            html.H2('Loss Development Factor'),
            table_ldf,
            html.Br(),
            
            html.H2('Cumulative Development Factor'),
            table_cdf, 
            
            html.Hr(),
            html.H1('SAVED PARAMETERS',id='saved_parameters'),
            table_log, 
            html.Button('DELETE', id='delete', n_clicks=0, className="btn btn-danger"),
            html.Button('PROCEED to STEP TWO', id='process', n_clicks=0, className="btn btn-success"),
            html.P(id='queued')
            ]),
            
       ],style = CONTENT_STYLE)
footer = html.Div([
                  html.P('Power by Marcus LEgacy')],
                  style =FOOTER_STYLE )

layout = html.Div([
                nav,
                sidebar,
                content,
                footer
                ])


@app.callback(
    [Output('risk_group', 'options'),
    Input('product_code_claim', 'value')]
    )
def update_dropdown(product_code_claim):
    index = IBNR.Triangles.index
    index['PRODUCT_CODE_CLAIM'] = index['PRODUCT_CODE_CLAIM'].astype(int).astype(str)
    
    b = index['RISK_GROUP'].loc[index['PRODUCT_CODE_CLAIM'].isin(product_code_claim)].sort_values().unique()
    options = [[{'label': i, 'value': i} for i in b]]

    return options

@app.callback(
    [Output('params_history', 'data')],
    
    [Input('saved', 'n_clicks'),
    Input('delete', 'n_clicks'),
    Input('product_code_claim', 'value'),
    State('params_history', 'selected_rows'),
    State('risk_group', 'value'),
    State('claim_category', 'value'),
    State('ibnr_methods', 'value'),
    State('drop_valuation', 'value'),
    State('drop_coordinate', 'value')]
    )
def saved_params(saved, delete, product_code_claim, 
            selected_rows, risk_group, claim_category,
            ibnr_methods, drop_valuation, drop_coordinate):
    
    risk_group      = handle_blank(risk_group)
    drop_valuation  = handle_blank(drop_valuation)
    drop_coordinate = handle_blank(drop_coordinate)
    
    #param_hist = pd.DataFrame([], columns=['product_code_claim','risk_group','claim_category','params','updated_on'])
    param_hist = MyPickle.load('params_hist.pkl')
    
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
 
    if button_id == 'saved':
        #print('saved success')
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {'product_code_claim'    : str(product_code_claim),
                'risk_group'           : str(risk_group),
                'claim_category'       : str(claim_category),
                'params'               : str(edit_params(ibnr_methods, drop_valuation, drop_coordinate)),
                'updated_on'           : str(date_time)}        
        
        param_hist = param_hist.append(log, ignore_index=True)    
        MyPickle.dump(param_hist,'params_hist.pkl')    
        
    filter_param = param_hist.loc[ param_hist['product_code_claim']==str(product_code_claim) ].reset_index(drop=True)
    anti_set = param_hist.loc[ param_hist['product_code_claim']!=str(product_code_claim) ].reset_index(drop=True)
    
    if button_id == 'delete':
        #print('delete success')
        filter_param = filter_param.drop(selected_rows).reset_index(drop=True)
        param_hist = anti_set.append(filter_param, ignore_index=True)
        MyPickle.dump(param_hist,'params_hist.pkl')
    
    return [filter_param.to_dict('records')]

@app.callback(Output('queued','children'),          
    [Input('process', 'n_clicks'),
     State('params_history','data'),
     State('product_code_claim', 'value')]
    )
def process(process, data, product_code_claim):

    df = pd.DataFrame(data)
    
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
 
    if button_id == 'process':
        MyPickle.dump(df, 'work_queue.pkl')
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ['%s parameters are sent to work queue @%s '% (product_code_claim , date_time)]


@app.callback(
[Output('incremental triangle', 'columns'),
 Output('incremental triangle', 'data'),
 Output('incremental triangle', 'style_data_conditional'),
 Output('cummulative triangle', 'columns'),
 Output('cummulative triangle', 'data'),
 Output('cummulative triangle', 'style_data_conditional'),
 Output('valuation triangle', 'columns'),
 Output('valuation triangle', 'data'),
 Output('valuation triangle', 'style_data_conditional'),
 
 Output('graph', 'figure'),
 
 Output('ldf', 'data'),
 Output('ldf', 'columns'),
 Output('ldf', 'style_data_conditional'),
 Output('cdf', 'data'),
 Output('cdf', 'columns'),
 Output('cdf', 'style_data_conditional'),
 Output('df', 'data'),
 Output('df', 'columns'),
 Output('df', 'style_data_conditional'),
 
 Output('slider_lookback_period', 'children'),
 Output('slider_development_period', 'children')
 ],


[Input('product_code_claim', 'value'),
 Input('risk_group', 'value'),
 Input('claim_category', 'value'),
 Input('lookback_period', 'value'),
 Input('development_period', 'value'),
 Input('ibnr_methods', 'value'),
 Input('drop_valuation', 'value'),
 Input('drop_coordinate', 'value')])
def update_tables(product_code_claim, risk_group,
           claim_category, lookback_period, development_period,
           ibnr_methods, drop_valuation, drop_coordinate):
    ## Handle error        
    risk_group      = handle_blank(risk_group)
    drop_valuation  = handle_blank(drop_valuation)
    drop_coordinate = handle_blank(drop_coordinate)
    
    
    ## Call IBNR API to retrieve triangle
    triangle = IBNR.filter_(IBNR.Triangles,
                product_code_claim=product_code_claim, risk_group=risk_group, claim_category=claim_category
                )
    
    # Incremental triangle    
    incr_tri = triangle.incremental_triangle(
                     lookback_period=lookback_period, development_period=development_period
                 ).data.reset_index(
                     ).rename(columns ={ 'index':'Accident Period'})

    # Cummulative triangle
    cumm_tri = triangle.cumulative_triangle(
                     lookback_period=lookback_period, development_period=development_period
                 ).data.reset_index(
                     ).rename(columns ={ 'index':'Accident Period'})

    # Valuation triangle
    val_tri = triangle.valuation_triangle(
                     lookback_period=lookback_period
                 ).data.reset_index(
                     ).rename(columns ={ 'index':'Accident Period'})
    
    # turn index into string
    for each in [incr_tri, cumm_tri, val_tri]:
        each['Accident Period'] = each['Accident Period'].astype(str)
        
    # conditional formating
    incr_styles = discrete_background_color_bins(incr_tri)
    cumm_styles = discrete_background_color_bins(cumm_tri)
    val_styles = discrete_background_color_bins(val_tri)
    
    # Column names
    columns=[{"name": ['Development Period',i], "id": i,'type':'numeric', 'format': Format(group=',')} for i in incr_tri.columns[1:]]
    columns.insert(0,{"name": ['','Accident Period'], "id": 'Accident Period'})
    val_columns=[{"name": ['Accounting Period',i], "id": i,'type':'numeric', 'format': Format(group=',')} for i in val_tri.columns[1:]]
    val_columns.insert(0,{"name": ['','Accident Period'], "id": 'Accident Period'})    


    ## Development Factors
    params = edit_params(ibnr_methods, drop_valuation, drop_coordinate)
    df, ldf, cdf = triangle.ratio_selection(
                             param = params ,
                             lookback_period=lookback_period, development_period=development_period)
    
    df = df.data.reset_index().rename(columns ={ 'index':'Accident Period'})
    df['Accident Period'] = df['Accident Period'].astype(str)
    ldf = ldf.data
    cdf = cdf.data     
    
    ###########################################################################
    ## plotting 1/cdf 
    fig = go.Figure()
    
    # plot selection
    selected_inverse_cdf = 1/cdf.T        
    fig.add_traces(go.Scatter(
                            x=selected_inverse_cdf.index, y=selected_inverse_cdf['CDF'],
                            mode='lines+markers',
                            name='selection'
                            ))
    
    # plot benchmark
    for each in ['12m-weighted', '6m-weighted']:
        _params = edit_params(each, None, None)
        _df, _ldf, _cdf = triangle.ratio_selection(
                               param = _params ,
                               lookback_period=lookback_period, development_period=development_period)
        _inverse_cdf = 1/_cdf.data.T
        fig.add_traces(go.Scatter(
                                x=_inverse_cdf.index, y=_inverse_cdf['CDF'],
                                mode='lines+markers',
                                name=each
                                )
                     )
    fig.update_layout(title={'text':"Inversed Cumulative Development Factors",
                             'x': 0.5}, 
                      xaxis_title='Development Month',
                      yaxis_title="1/CDF")    
    
    ###########################################################################
    # conditional formating
    df_styles = discrete_background_color_bins(df)
    ldf_styles = discrete_background_color_bins(ldf)
    cdf_styles = discrete_background_color_bins(cdf)
    
    # Column names
    ldf_columns=[{"name":['Development Period', i], "id": i,'type':'numeric', 'format': Format(precision=4, scheme=Scheme.fixed)} for i in ldf.columns]
    cdf_columns=[{"name":i, "id": i,'type':'numeric', 'format': Format(precision=4, scheme=Scheme.fixed)} for i in cdf.columns]
    df_columns=[{"name": ['Development Period',i], "id": i,'type':'numeric', 'format': Format(precision=4, scheme=Scheme.fixed)} for i in df.columns[1:]]
    df_columns.insert(0,{"name": ['','Accident Period'], "id": 'Accident Period'})
    
    # Convert all dataframe to dictionary
    incr_data=incr_tri.to_dict('records') 
    cumm_data=cumm_tri.to_dict('records')
    val_data = val_tri.to_dict('records')
    ldf = ldf.to_dict('records')
    cdf = cdf.to_dict('records')
    df = df.to_dict('records')
    
    # Slider value
    slider_lookback_period = 'Lookback Period = {} '.format(lookback_period)
    slider_development_period = 'Development Period = {} '.format(development_period)
    
  
         
    return (columns, incr_data, incr_styles,
            columns, cumm_data, cumm_styles,
            val_columns, val_data, val_styles,
            fig,
            ldf, ldf_columns, ldf_styles,
            cdf, cdf_columns, cdf_styles,
            df, df_columns, df_styles,
            slider_lookback_period, slider_development_period

            )


