#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  4 19:34:48 2021

@author: marcus
"""
import pandas as pd
import numpy as np


from app import IBNR, cl, MyPickle, html, dbc, dash_table, Format, Scheme

NAV_STYLE = {
            "height": 10,
            "padding": "2rem 1rem",
            }
CONTENT_STYLE = {
        "padding": "5rem 1rem",
        }
nav = dbc.Nav([ html.H2(children="I.B.N.R.", style={"color":"#fff", "margin-right": "2rem"}),               
                dbc.NavItem(dbc.NavLink("Step One ", href="/step_one")),
                dbc.NavItem(dbc.NavLink("Step Two ", active=True, href="/step_two")),
                ], 
                pills=True,
                className="navbar navbar-expand-lg navbar-dark bg-primary fixed-top",       
                style = NAV_STYLE
            )

def _get_paid_df_ult_ibnr_M2Qper(param_hist):    
    df = IBNR.Data_Handler.data
    output = pd.DataFrame([])
    for i, row in param_hist.iterrows():
        product_code_claim  = eval(row['product_code_claim'])
        claim_category      = eval(row['claim_category'])
        risk_group          = eval(row['risk_group'])
        param               = eval(row['params']) 
        
        # fit model with selected parameter
        model = cl.Development(**param)
        triangle_1D = IBNR.filter_(IBNR.Triangles,
            product_code_claim=product_code_claim, risk_group=risk_group, claim_category=claim_category
            ).triangle_1D
        model.fit(triangle_1D.incr_to_cum())
        
        cdf = np.insert( model.cdf_.T[::-1].values, [0], 1)
        
        
        # get paid amount from imported data
        filter1 = df['PRODUCT_CODE_CLAIM'].isin(product_code_claim)
        filter2 = df['CLAIM_CATEGORY'].isin(claim_category)
        if risk_group == None:
            paid = df.loc[ (filter1) & (filter2)]
            risk_group=['ALL']
        else:
            filter3 = df['RISK_GROUP'].isin(risk_group)
            paid = df.loc[ (filter1) & (filter2) & (filter3) ]
        
        key = claim_category[0]+risk_group[0]
        paid = pd.pivot_table(paid, index=['ACCIDENT_MONTH_DATE'], aggfunc={'CLAIM_PAID_EX_GST_D':'sum'})
        paid.columns = ['1.PAID:%s' %key]
        paid.index = paid.index.to_period("M")
        
        # create multilevel index
        idx = triangle_1D.T.columns
        idx2 = idx.to_timestamp().to_period("Q")
        index = pd.MultiIndex.from_arrays([idx,idx2], names=['M', 'Q'])

        # join paid data to multi-index dataframe
        cluster = pd.DataFrame(index = index)
        cluster = cluster.join(paid, on=['M'])
        
                
        # calculate ULT / IBNR 
        paid = cluster['1.PAID:%s' %key]
        ultimate = cdf * paid
        ibnr = ultimate - paid
        
        cluster['2.DF:%s' %key] = cdf
        cluster['3.ULT:%s' %key] = ultimate
        cluster['4.IBNR:%s' %key] = ibnr
      
        
        #calculate monthly percentage over quarter
        quarter_ibnr = cluster.reset_index(level='Q')['4.IBNR:%s' %key].resample('Q', convention='end').agg('sum')
        quarter_paid = cluster.reset_index(level='Q')['1.PAID:%s' %key].resample('Q', convention='end').agg('sum')
        cluster = pd.merge(cluster, quarter_ibnr, how='left', left_on=['Q'], right_index=True, suffixes=('_m','_q'))
        cluster = pd.merge(cluster, quarter_paid, how='left', left_on=['Q'], right_index=True, suffixes=('_m','_q'))
        cluster['percent_M/Q:%s' %key] = cluster['4.IBNR:%s_m' %key].div(cluster['4.IBNR:%s_q' %key]).replace((np.inf, -np.inf, np.nan), (1/3, 1/3, 1/3))
        
        # Multilevel columns name
        cluster.columns = [ claim_category*7, risk_group *7, list(cluster.columns)]
    
        # append all cluster to one table
        output = pd.concat([output,cluster], axis=1)
    return output

def cal_QUARTERLY_percent_over_portfolio(output, key):
    # get quarterly numbers from every groups except 'All'
    # Note: default group "ALL" does not required allocation
    q_all = output.iloc[:, (output.columns.get_level_values(1) !='ALL') &
                           (output.columns.get_level_values(2).str.contains(key)) &
                            (output.columns.get_level_values(2).str.contains('_q'))]
    
    # sum over portfolio
    sum_q_all = q_all.sum(axis=1)
    
    # get percentage over portfolio
    percent_over_port = q_all.div(sum_q_all, axis=0)
    return percent_over_port

def update_layout():
    
    # load parameter from webapp
    param_hist = MyPickle.load('work_queue.pkl')
    # get all paid, df, ultimate, ibnr from data 
    output = _get_paid_df_ult_ibnr_M2Qper(param_hist)
    
    # calculate quarterly proportion over portfolio
    percent_ibnr_over_portfolio = cal_QUARTERLY_percent_over_portfolio(output, 'IBNR') 
    percent_paid_over_portfolio = cal_QUARTERLY_percent_over_portfolio(output, 'PAID')
    
    # impute ibnr with paid when null
    percent_paid_over_portfolio.columns = percent_ibnr_over_portfolio.columns 
    per_Over_port = percent_ibnr_over_portfolio.combine_first(percent_paid_over_portfolio)
    
# =============================================================================
#     CALCULATE ALLOCATION PERCENTAGE
#     Methods:
#     1. Find column with name "month to quarter percentage" from "output".
#     2. Multiply the above with proportion of the portfolio when it is a subset of the portfolio (risk cluster),
#        otherwise use the month to quarter percentage. 
# =============================================================================
    level0 = output.columns.get_level_values(0)
    level1 = output.columns.get_level_values(1)
    level2 = output.columns.get_level_values(2)
    
    a = level2.str.contains('percent_M/Q')  
    for i,x in enumerate(a):
        if x ==True: # This is #1
            key = level0[i] + level1[i]
            
            if level1[i] != 'ALL': # this is #2 (only active when it is a risk cluster)
                col = per_Over_port.columns.get_level_values(1).get_loc(level1[i]) # column id of the risk cluster
                
                percent_M_over_Q = output.iloc[:, i]
                per_Over_port_i = per_Over_port.iloc[:, col]
                percent_allocation = percent_M_over_Q * per_Over_port_i   
                
                output[level0[i] ,level1[i],'percent_over_portfolio:%s' %key] =  per_Over_port_i         
                output[level0[i] ,level1[i],'5.ALLOCATION:%s' %key]               =   percent_allocation    
            else:
                output[level0[i] ,level1[i],'5.ALLOCATION:%s' %key] =  output[(level0[i], level1[i], 'percent_M/Q:%s' %key)]     
                
    output = output.sort_index(axis=1)
    
    
    ## Formating in APP
    # drop unnecessary colomun that not render
    drop_col = output.filter(regex=r'(percent| *_q)').columns
    output.drop(drop_col, axis=1, inplace=True)
    
    # convert index to string for rendering
    output.reset_index(level='Q', drop =True, inplace=True)  # drop the quarterly index which no longer use
    output = output.reset_index(level='M').rename(columns ={ '' : 'Accident Period', 'M':'Accident Period'})
    output['Accident Period'] = output['Accident Period'].astype(str)
    
# =============================================================================
#     compile dictionary for APP
# =============================================================================
    level0 = output.columns.get_level_values(0)
    level1 = output.columns.get_level_values(1)
    level2 = output.columns.get_level_values(2)
    output.columns = output.columns.droplevel([0,1])
    
    columns = []
    for i in zip(level0, level1, level2):
        
        if i[0] == 'Accident Period': # cater format for index
            col = {'name' : [i[0], i[1],i[2]],
                   'id'   :  i[2],
                   'type' : 'text'
                   }
        else :
            col = {'name' : [i[0], i[1],
                            i[2].split(":")[0].split(".")[1]],
                   'id'   : i[2],
                   'type' : 'numeric'
                   }

        if 'DF' in i[2]:
            col['format'] = Format(precision=3, scheme=Scheme.fixed)
        elif 'ALLOCATION' in i[2]:
            col['format'] = Format(precision=3, scheme=Scheme.percentage)
        elif 'percent' in i[2]:
            col['format'] = Format(precision=3, scheme=Scheme.percentage)
        else:
            col['format'] = Format(group=',', precision=0, scheme=Scheme.fixed)
            
        columns.append(col)
    output.fillna(0, inplace=True)    
    output = output.to_dict('records')
    
# =============================================================================
#     place information into html
# =============================================================================
    table_ultimate = html.Div([
                              dash_table.DataTable(
                                id='ultimate',
                                columns=columns,
                                data=output,
                                editable=True,
                                sort_action="native",
                                export_format="csv",
                                merge_duplicate_headers=True,
                                #style_data_conditional = None,
                                style_header={
                                    'fontWeight': 'bold',
                                    'textAlign': 'center'
                                    },
                                style_table={'minWidth': '100%',
                                            'overflowX': 'auto'},
                                fixed_columns={'headers': True, 'data': 1}
                                )
                            ])



    content = html.Div([
                        table_ultimate
                        ], style= CONTENT_STYLE)
    
    layout = html.Div([
                       nav,
                       content,
                       ])

    return  layout