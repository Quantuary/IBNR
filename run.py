#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  4 16:45:09 2021

@author: marcus
"""
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import step1, step2


app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    html.Div(id='page-content', children=[])
])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    
    if pathname == '/':
        return step1.layout
    
    if pathname == '/step_two':
        return step2.update_layout()
    else:
        return step1.layout


if __name__ == '__main__':
    app.run_server(host='0.0.0.0',debug=False, port=5002)
    
    
   