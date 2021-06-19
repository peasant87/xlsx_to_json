#!/usr/bin/env python3

import sys
import os
import pandas as pd
import numpy as np
import ast
import json

MODEL_ID = 'merchant_product_model_id'
CONFIG_ID = 'merchant_product_config_id'
SIMPLE_ID = 'merchant_product_simple_id'

def prepare_product_model_dict(MODEL_ID, list_sheets):
    product_model_dict = list_sheets[0].set_index(MODEL_ID,drop=False).to_dict(orient='index')#list_sheets[0].set_index(MODEL_ID).to_dict(orient='index')
    return product_model_dict

def prepare_product_dict(product_model_dict, list_sheets):
    for model in product_model_dict:
        product_config_dict = prepare_config_dict(model,list_sheets)
        
        if(product_config_dict):
            product_config_dict = prepare_media_simple_dict(product_config_dict,list_sheets)
            
        product_model_dict[model]['product_config'] = product_config_dict
    return product_model_dict

def prepare_config_dict(model_id,list_sheets):
    product_config_indexed = list_sheets[1].set_index(MODEL_ID)
    if(model_id in product_config_indexed.index):
        product_config = product_config_indexed.loc[model_id]
        if(isinstance(product_config,pd.DataFrame)):
            product_config_dict = product_config.set_index(CONFIG_ID,drop=False).to_dict(orient='index')
        elif(isinstance(product_config,pd.Series)):
            product_config_dict = product_config.to_frame().T.set_index(CONFIG_ID,drop=False).to_dict(orient='index')
    else:
        product_config_dict = {}

    return product_config_dict

def prepare_media_simple_dict(product_config_dict,list_sheets):
    media_df, product_simple_df = set_index(CONFIG_ID,list_sheets)
    
    for config in product_config_dict:
        if(config in media_df.index):
            df = media_df.loc[config]
            if(isinstance(df,pd.Series)):
                df = df.to_frame().T
            media_dict = df[df.columns[2:]].to_dict(orient='records')
            product_config_dict[config]['media'] = media_dict
        else:
            product_config_dict[config]['media'] = []
            
        if(config in product_simple_df.index):
            df = product_simple_df.loc[config]
            if(isinstance(df,pd.Series)):
                df = df.to_frame().T
            product_simple_dict = df.set_index(SIMPLE_ID,drop=False).to_dict(orient='index')
            product_config_dict[config]['product_simple'] = product_simple_dict
        else:
            product_config_dict[config]['product_simple'] = []   
    return product_config_dict

def set_index(index_name,list_sheets):
    return [list_sheets[2].set_index([index_name]),list_sheets[3].set_index([index_name])]

def data_type_definition(index,key,value,list_dicts):
    if list_dicts:
        type = list_dicts[index][key]
        if (type.lower() == 'string' or type.lower() == 'str'):
            return str(value)
        elif (type.lower() == 'string_list' or type.lower() == 'list_string'):
            return value.split(',')
        elif (type.lower() == 'number' or type.lower() == 'int'):
            if value:
                return int(value)
            else:
                return value
        elif (type.lower() == 'json'):
            try:
                return ast.literal_eval(value)
            except:
                print(error_message(index,key,value))
        else:
            print(error_message(index,key,value))       
    else:
        try:
            return ast.literal_eval(value)
        except:
            pass
        return value

def create_product_json(products_dicts,list_dicts):
    for product_id,product in products_dicts.items():
        product_dict = {'outline':'','product_model':{'product_model_attributes':{}}}
        
        for key, value in product.items():
            product_model = product_dict['product_model']
            product_model_attributes = product_model['product_model_attributes']
            if key == 'outline':
                product_dict[key] = data_type_definition(0,key,value,list_dicts) #model.pop('outline')
                continue
            if "_id" in key:
                product_dict[key] = data_type_definition(0,key,value,list_dicts) #model.pop('outline')
                continue
            if isinstance(value,dict):
                product_model[key] = new_product_config(value,list_dicts)
                continue
            product_model_attributes[key] = data_type_definition(0,key,value,list_dicts)

        save_json(product_dict,product_id)

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

def save_json(product_dict,id):
    outline = product_dict.get('outline') if product_dict.get('outline') else ''
    filename = "./output_json/{}_{}.json".format(outline,id)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as outfile:
        json.dump(product_dict, outfile, indent=4, cls=NpEncoder,ensure_ascii=False)
    print("Saved JSON file at: ",filename)

def new_product_config(product_config,list_dicts):
    product_config_list = []
    for config in product_config.values():
        config_dict = {'product_config_attributes':{}}
        #model = products_dicts[product_id]
        product_config_attributes = config_dict['product_config_attributes']
        for key, value in config.items():
            if "_id" in key:
                config_dict[key] = data_type_definition(1,key,value,list_dicts) #model.pop('outline')
                continue
            if isinstance(value,list):
                for v in value:
                    if isinstance(v,dict):
                        for _k,_v in v.items():
                            v[_k] = data_type_definition(2,_k,_v,list_dicts)
                product_config_attributes[key] = value
                continue
            if isinstance(value,dict):
                config_dict[key] = new_product_simple(value,list_dicts)
                continue
            product_config_attributes[key] = data_type_definition(1,key,value,list_dicts)
        product_config_list.append(config_dict)

    return product_config_list

def error_message(sheet,column,value):
    return '''
### WARNING ###
Wrong type informed!
Sheet: {}
Column: {}
Value: {}

    The type must be string, json, string_list or number
'''.format(sheet,column,value)

def error_message_header(header_length):
    return '''
### ERROR ###
Invalid header length: {}
Orientation: Insert a valid header length
'''.format(header_length)

def new_product_simple(product_simple,list_dicts):
    product_simple_list = []
    for simple in product_simple.values():
        simple_dict = {'product_simple_attributes':{}}
        
        for key,value in simple.items():
            product_simple_attributes = simple_dict['product_simple_attributes']
            if "_id" in key:
                simple_dict[key] = data_type_definition(3,key,value,list_dicts) #model.pop('outline')
                continue
            product_simple_attributes[key] = data_type_definition(3,key,value,list_dicts)
        product_simple_list.append(simple_dict)

    return product_simple_list

def validate_header(header_length):
    try:
        int(header_length)
    except:
        error_message_header(header_length)

def sheet_preprocessing(file, sheet, header_length=0):
    validate_header(header_length)
    dict_index = {}
    #TODO: improve with read_excel, sheet_name=None
    df = pd.read_excel(file,sheet_name=sheet)
        
    #removing unnamed and comment columns
    cols = df.columns[~df.columns.str.startswith(('Unnamed:',"#"))]
    df = df[cols]

    if(header_length):
        #save data type into dict
        dict_index = data_type_dict(df)
        df = df.drop(0).reset_index(drop=True)

    #removing 'nan' values and replacing with empty string ('')
    df.fillna('',inplace=True)

    return df,dict_index

def data_type_dict(df):
    columns = df.columns
    data_types = list(df.iloc[0])
    if (len(columns) == len(data_types)):
        return dict(zip(columns,data_types))
    else:
        raise Exception('Error in datatype rows')

#TODO: improve with argparse
file = sys.argv[1]
if len(sys.argv) > 2:
    header_length = sys.argv[2]
else: 
    header_length = 0

print("Reading file: ",file)
sheets = pd.ExcelFile(file)

list_sheets = []
list_dicts = []
print("Reading sheets...")
for sheet in sheets.sheet_names:
    print("Found sheet: ",sheet)
    df,dict_index = sheet_preprocessing(file, sheet, header_length)
    
    if(dict_index):
        list_dicts.append(dict_index)

    list_sheets.append(df)

print("Preparing file...")
product_model_dict = prepare_product_model_dict(MODEL_ID, list_sheets)
final_dict = prepare_product_dict(product_model_dict,list_sheets)
print("Creating JSON file...")
create_product_json(final_dict,list_dicts)