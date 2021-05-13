# -*- coding: utf-8 -*-
"""
Created on Mon Dec 14 22:41:40 2020

@author: mleong
"""
import os
#os.chdir(r"R:\Technical\04 Actuarial Pricing\Technical Analytics\travel\notebooks\Marcus's")
#os.chdir(r"/home/marcus/Documents/git/IBNR")
from Data_Handler import Data_Handler 

import chainladder as cl
import pandas as pd
import numpy as np


               


        
class Data_Handler(Data_Handler):
    
    @classmethod    
    def pretty_print(cls, date):
        '''
        Print given date in pretty format.
        '''
        
        print('%s-%s ' % (date.strftime("%B"), date.strftime('%Y') ))
    
    def __init__(self):
        self.data = Data_Handler.import_data('data.sql')
        self.latest_date = max(self.data.ACCOUNTING_MONTH_DATE)
        self.earliest_date = min(self.data.ACCOUNTING_MONTH_DATE)
     
    def groupby(self, columns, from_=None, to_=None):
        if from_==None:
           return self.data.groupby(columns).agg({'CLAIM_PAID_EX_GST_D':'sum'}).round(0)
       
        else:
            condition=(self.data['ACCOUNTING_MONTH_DATE']>=from_) & (self.data['ACCOUNTING_MONTH_DATE']<=to_)             
            return self.data[condition].groupby(columns).agg({'CLAIM_PAID_EX_GST_D':'sum'}).round(0)
            

    
class filter_(object):

    
    def __init__(self, Triangles, product_code_claim=None, claim_category=None, 
                 claim_category_reserving=None, client_name=None, risk_group=None,
                 product_group=None, product_code=None):
        
        self.triangle_mD = Triangles
        
        self.product_code_claim = product_code_claim
        self.claim_category = claim_category
        self.claim_category_reserving = claim_category_reserving
        self.client_name = client_name
        self.risk_group = risk_group
        #self.product_group = product_group
        #self.product_code = product_code
        
        self.triangle_1D = self._filter()
        self.shape = self.triangle_1D.shape
        

    def _filter(self):
        triangle_incremental = self.triangle_mD
        for (column_name, items) in [('PRODUCT_CODE_CLAIM', self.product_code_claim),
                                    ('CLAIM_CATEGORY', self.claim_category),
                                    ('CLAIM_CATEGORY_RESERVING', self.claim_category_reserving),
                                    ('CLIENT_NAME', self.client_name),
                                    ('RISK_GROUP', self.risk_group)
                                    #('PRODUCT_GROUP', self.product_group),
                                    #('PRODUCT_CODE', self.product_code)                          
                                    ]:
    
            if items is not None:
                triangle_incremental = triangle_incremental[triangle_incremental[column_name].isin(items)]
            else:
                continue
    
        
        if len(triangle_incremental.index) > 1:
            triangle_incremental = triangle_incremental.sum()
        else:
            triangle_incremental
        
        return triangle_incremental
 

    def valuation_triangle(self, lookback_period=12):
        df = self.triangle_1D.dev_to_val().to_frame()
        df = df.iloc[-lookback_period:, -lookback_period:]
        df.name = 'Valuation Triangle'
        return IBNR.format_amount(df)
    
    def incremental_triangle(self, lookback_period=12, development_period=12):
        df = self.triangle_1D.cum_to_incr().to_frame()                          # turn triangle to pandas data frame
        df = df.iloc[-lookback_period:, :development_period]   # cut the period to display
        df.name = 'Incremental Developmenet Triangle'
        return IBNR.format_amount(df)
    
    def cumulative_triangle(self, lookback_period=12, development_period=12):
        df = self.triangle_1D.incr_to_cum().to_frame()
        df = df.iloc[-lookback_period:, :development_period]
        df.name = 'Cumulative Developmenet Triangle'
        return IBNR.format_amount(df)
        
    
    def link_ratio(self, lookback_period=12, development_period=12):
        df = self.triangle_1D.incr_to_cum().link_ratio.to_frame()   #link ratio API must take cumulative triangle
        df = df.iloc[-lookback_period:, :development_period]
        df.name = 'Development Factor'
        return IBNR.format_ratio(df)
         

    def all_ldf_cdf(self, development_period=12):
        
        ldf = pd.DataFrame()
        cdf = pd.DataFrame()
        for label in IBNR.model_params:
            param = IBNR.model_params[label]
            
            model = cl.Development(**param).fit(self.triangle_1D.incr_to_cum())
            _ldf = model.ldf_.to_frame()
            _ldf.rename(index={'(All)':label}, inplace=True)
            ldf = ldf.append(_ldf)
            
            _cdf = model.cdf_.to_frame()
            _cdf.rename(index={'(All)': label}, inplace=True)
            cdf = cdf.append(_cdf)
        
        s_ldf, s_cdf = filter_.sample_weighted_80_20_6m_12m(self.triangle_1D)
        s_ldf.columns = _ldf.columns
        s_cdf.columns = _cdf.columns
        
        ldf = ldf.append(s_ldf)
        ldf = ldf.iloc[:,:development_period]
        ldf.name = 'Loss Development Factor'
        
        cdf = cdf.append(s_cdf)
        cdf = cdf.iloc[:,:development_period]
        cdf.name = 'Cumulative Development Factor'
        
        return IBNR.format_table(ldf) , IBNR.format_table(cdf)

        

    def ratio_selection(self, param=None, lookback_period=12, development_period=12):
        transformed_triangle = cl.Development(**param).fit_transform(self.triangle_1D.incr_to_cum())
        
        ldf = transformed_triangle.ldf_.to_frame()
        ldf =ldf.iloc[:,:development_period]
        ldf.rename(index={'(All)':'LDF'}, inplace=True)
        ldf.name = 'Loss Development Factor'
        
        cdf = transformed_triangle.cdf_.to_frame()
        cdf =cdf.iloc[:,:development_period]
        cdf.rename(index={'(All)':'CDF'}, inplace=True)
        cdf.name = 'Cumulative Development Factor'
        
        
        df = transformed_triangle.link_ratio.to_frame()
        df = df.iloc[-lookback_period:, :development_period]
        df.name = 'Selected Development Factor'
        
        return IBNR.format_ratio(df), IBNR.format_ratio(ldf), IBNR.format_ratio(cdf)
    
    @classmethod
    def sample_weighted_80_20_6m_12m(cls, triangle_1D):
        param6 = {'n_periods':6, 'average':'simple'}
        param12 = {'n_periods':12, 'average':'simple'} 
        
        model6 = cl.Development(**param6).fit(triangle_1D.incr_to_cum())
        model12 = cl.Development(**param12).fit(triangle_1D.incr_to_cum())
        
        def generate_sample_weight(model, value):
            weight = model.w_
            new_weight = weight.reshape(-1,1)
            new_weight[new_weight ==1] = value
            new_wewight = new_weight.reshape(model.w_.shape[2],model.w_.shape[3])
            return new_wewight
        weight6 = generate_sample_weight(model6, 0.8)
        weight12 = generate_sample_weight(model12, 0.2) 
        
        param = {'n_periods':12, 'average':'simple'} 
        selected_link = cl.Development(**param).fit_transform(triangle_1D.incr_to_cum()).link_ratio.to_frame().values
        
        
        weight_80_20 = np.where(weight6==0, weight12, weight6 )                        # making 80 20 sample weight
        weight_80_20 = weight_80_20[:selected_link.shape[0], :selected_link.shape[0]]  # reshape to align with link ratio
        weight_80_20[np.isnan(selected_link)] = 0                                      # delete the extra diagonal where no link ratio
        
        product = np.multiply(weight_80_20, selected_link)                             # mutiple two matrix together
        n = np.nansum(product, axis=0)                                                 # sum by columns
        d = np.nansum(weight_80_20, axis=0)                                            # sum weight
        ldf = pd.DataFrame(np.divide(n, d)).T.rename(index={0:'80/20-6m/12m-sample-weighted'})                  # divide by denominator(weight) then transpose and rename
        
        
        cdf = ldf[ldf.columns[::-1]].cumprod(axis=1)                                   # calculate cumulative factor
        cdf = cdf[cdf.columns[::-1]]
    
        return ldf, cdf
        
    
class IBNR():   
    model_params={'3m-weighted' : {'n_periods' : 3,'average':'volume'},
                 '3m-simple'   : {'n_periods' : 3,'average':'simple'},
             
                 '4m-weighted' : {'n_periods' : 4,'average':'volume'},                    
                 '5m-weighted' : {'n_periods' : 5,'average':'volume'},
                 '6m-weighted' : {'n_periods' : 6,'average':'volume'},
                 '6m-simple'   : {'n_periods' : 6,'average':'simple'},
                 
                 '7m-weighted'         : {'n_periods' : 7,'average':'volume'},
                 '8m-weighted'         : {'n_periods' : 8,'average':'volume'},
                 '9m-weighted'         : {'n_periods' : 9,'average':'volume'},
                 '10m-weighted'        : {'n_periods' : 10,'average':'volume'},
                 '11m-weighted'        : {'n_periods' : 11,'average':'volume'},
                 '12m-weighted'        : {'n_periods' : 12,'average':'volume'},
                 #'12m-weighted-drops'  : {'n_periods' : 12,'average':'volume','drop_high':True, 'drop_low':True},
                 '12m-simple'          : {'n_periods' : 12,'average':'simple'},
       
                 '15m-weighted'        : {'n_periods' : 15,'average':'volume'},
                 '18m-weighted'        : {'n_periods' : 18,'average':'volume'},
                 '24m-weighted'        : {'n_periods' : 24,'average':'volume'},
                 #'24m-weighted-drops'  : {'n_periods' : 24,'average':'volume','drop_high':True, 'drop_low':True},
                 '24m-simple'          : {'n_periods' : 24,'average':'simple'},
       
                 '36m-weighted'        : {'n_periods' : 36,'average':'volume'},
                 #'36m-weighted-drops'  : {'n_periods' : 36,'average':'volume','drop_high':True, 'drop_low':True},
                 '36m-simple'          : {'n_periods' : 36,'average':'simple'},
                 'All-weighted'        : {'n_periods' : -1,'average':'volume'},    
                }
    
    
    def __init__(self):
        self.Data_Handler = Data_Handler()
        '''
        Using the chainladder (cl) package: https://chainladder-python.readthedocs.io/en/latest/index.html
        '''
        self.Triangles = cl.Triangle(self.Data_Handler.data , origin='ACCIDENT_MONTH_DATE', 
                                    development='ACCOUNTING_MONTH_DATE', columns='CLAIM_PAID_EX_GST_D',
                                    index=['PRODUCT_CODE_CLAIM','CLAIM_CATEGORY', 'CLAIM_CATEGORY_RESERVING',
                                           'CLIENT_NAME', 'RISK_GROUP'
                                           #'PRODUCT_GROUP'
                                           ],
                                    cumulative=False
                                    )
        self.filter_ = filter_


    @classmethod
    def format_amount(cls, df):
        return df.fillna(0).round(0).astype(int).style.format("{:,}"
                    ).set_caption(df.name).set_table_styles([{'selector': 'caption',
                                                              'props': [('color', 'blue'),
                                                                        ('text-align', 'center'),
                                                                        ('font-size', '16px')
                                                                        ]
                                                              }]
                    ).background_gradient(cmap='Reds', axis = None) 
                                                             
    @classmethod
    def format_ratio(cls, df):
        return df.fillna(0).round(5).style.format("{:,}"
                    ).set_caption(df.name).set_table_styles([{'selector': 'caption',
                                                              'props': [('color', 'blue'),
                                                                        ('text-align', 'center'),
                                                                        ('font-size', '16px')
                                                                        ]
                                                              }]
                    ).background_gradient(cmap='Reds', axis = None) 
    @classmethod
    def format_table(cls, df):
        return df.fillna(0).round(5).style.format("{:,}"
                    ).set_caption(df.name).set_table_styles([{'selector': 'caption',
                                                              'props': [('color', 'blue'),
                                                                        ('text-align', 'center'),
                                                                        ('font-size', '16px')
                                                                        ]
                                                              }]
                    ).background_gradient(cmap='coolwarm', axis = 0) 
        

