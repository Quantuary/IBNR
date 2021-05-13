# -*- coding: utf-8 -*-
"""
Created on Mon Feb  8 15:21:15 2021

@author: mleong
"""
import pandas as pd
import cx_Oracle
#import MyPickle


class Data_Handler():

    @classmethod
    def import_data(cls, script_path):
        ''' 
        Importing data into pandas data frame via oracle SQL connection
        '''
        password = Data_Handler.read_strfile('Password.txt')
        connection = cx_Oracle.connect("actuary",password,
                                       cx_Oracle.makedsn("auwphprx-scan.maau.group",
                                                         1521,
                                                         "Dwin"))
        query = Data_Handler.read_strfile(script_path)
        df  = pd.read_sql_query(query, con=connection)
        
        connection.close()
        #df = MyPickle.load("a.pkl")
        return df 
    
    @classmethod
    def read_strfile(cls, path):
        ''' 
        Convert text file into a string
        '''
        f = open(path, 'r')
        string = f.read()
        f.close()
        return string 
    
    @classmethod
    def pandas_to_sql(cls,df,sql_table_name):
        '''
        Upload pandas dataframe to existing table on oracle database.
        CAUTIOMS: This function will truncate the existing table and replace with the uploaded data.
        '''
        password = Data_Handler.read_strfile('Password.txt')
        connection = cx_Oracle.connect("actuary",password,
                                       cx_Oracle.makedsn("auwphprx-scan.maau.group",
                                                         1521,
                                                         "Dwin"))
        
        ls = [tuple(x) for x in df.values]
        column_str = ','.join(list(df))
        insert_str = ','.join([':'+each for each in list(df)])
        final_str = "INSERT INTO actuary.%s (%s) VALUES (%s)" % \
                      (sql_table_name,column_str,insert_str)
        
        cursor=connection.cursor()
        cursor.execute('''Truncate Table %s''' % (sql_table_name))
        cursor.executemany(final_str,ls)
        connection.commit()   
        connection.close()
        
