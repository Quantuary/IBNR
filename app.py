#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  4 16:31:26 2021

@author: marcus
"""
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_table
from dash_table.Format import Format, Scheme
from dash.dependencies import Input, Output, State

import MyPickle
from IBNR import IBNR, cl
IBNR = IBNR()

app = dash.Dash(__name__,
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}])
app.title = 'I.B.N.R'
server = app.server