#!/usr/bin/env python3

import sys
import os
import pandas as pd
import numpy as np
import ast
import json
from collections import OrderedDict

MODEL_ID = 'merchant_product_model_id'
CONFIG_ID = 'merchant_product_config_id'
SIMPLE_ID = 'merchant_product_simple_id'

def prepare_product_model_dict(MODEL_ID, df):
    product_model_dict = df.set_index(MODEL_ID,drop=False).to_dict(orient='index') #list_sheets[0].set_index(MODEL_ID).to_dict(orient='index')
    return product_model_dict

def prepare_product_dict(dfs_dict):
    list_keys_dfs_dict = list(dfs_dict.keys())
    product_model_dict = prepare_product_model_dict(MODEL_ID,dfs_dict[list_keys_dfs_dict[0]])

    for model in product_model_dict:
        config_key = list_keys_dfs_dict[1]
        product_config_dict = prepare_config_dict(model,dfs_dict[config_key])
        
        if(product_config_dict):
            keys = list_keys_dfs_dict[2:]
            product_config_dict = prepare_config_childs(product_config_dict,dfs_dict,keys)
            
        product_model_dict[model][config_key] = product_config_dict
    return product_model_dict

def prepare_config_dict(model_id,df):
    product_config_indexed = df.set_index(MODEL_ID)
    if(model_id in product_config_indexed.index):
        product_config = product_config_indexed.loc[model_id]
        if(isinstance(product_config,pd.DataFrame)):
            product_config_dict = product_config.set_index(CONFIG_ID,drop=False).to_dict(orient='index')
        elif(isinstance(product_config,pd.Series)):
            product_config_dict = product_config.to_frame().T.set_index(CONFIG_ID,drop=False).to_dict(orient='index')
    else:
        product_config_dict = {}

    return product_config_dict

def prepare_config_childs(product_config_dict,dfs,sheets_names):
    for config in product_config_dict:
        for sheet_name in sheets_names:
            df = dfs[sheet_name].set_index([CONFIG_ID])
            #df = df.set_index([CONFIG_ID])
            if(config in df.index):
                df = df.loc[config]
                if isinstance(df,pd.Series):
                    df = df.to_frame().T
                if 'media' in sheet_name:
                    df_dict = df[df.columns[2:]].to_dict(orient='records')
                else:
                    df_dict = df.set_index(SIMPLE_ID,drop=False).to_dict(orient='index')
                product_config_dict[config][sheet_name] = df_dict
            else:
                product_config_dict[config][sheet_name] = []
    return product_config_dict

def data_type_definition(sheet_name,key,value,dict_data_types):
    if dict_data_types:
        type = dict_data_types.get(key)
        if type:
            if (type.lower() == 'string' or type.lower() == 'str'):
                return str(value)
            elif (type.lower() == 'string_list' or type.lower() == 'list_string'):
                return value.split(',')
            elif (type.lower() == 'number' or type.lower() == 'int'):
                try:
                    if value:
                        return int(value)
                    else:
                        return value
                except:
                    print(error_message(sheet_name,key,type,value))
                    sys.exit(1)
            elif (type.lower() == 'json'):
                try:
                    return ast.literal_eval(value)
                except:
                    print(error_message(sheet_name,key,type,value))
                    sys.exit(1)
            else:
                print(error_message(sheet_name,key,type,value))       
                sys.exit(1)
        else:    
            print(error_message(sheet_name,key,type,value))       
            sys.exit(1)
    else:
        try:
            return ast.literal_eval(value)
        except:
            pass
        return value

def create_product_json(products_dicts,dict_data_types):
    sheet_name = next(iter(dict_data_types.keys()))
    json_name = sheet_name[:-1]
    attributes = json_name+'_attributes'
    data_types = dict_data_types.pop(sheet_name)
    product_dict = {'outline':'',json_name:{attributes:{}}}
    for product_id,product in products_dicts.items():        
        for key, value in product.items():
            product_model = product_dict[json_name]
            product_model_attributes = product_model[attributes]
            if key == 'outline':
                product_dict[key] = data_type_definition(sheet_name,key,value,data_types) #model.pop('outline')
                continue
            if "_id" in key:
                product_dict[key] = data_type_definition(sheet_name,key,value,data_types) #model.pop('outline')
                continue
            if isinstance(value,dict):
                product_model[key] = new_product_config(value,dict_data_types.copy())
                continue
            product_model_attributes[key] = data_type_definition(sheet_name,key,value,data_types)

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

def new_product_config(product_config,dict_data_types):
    product_config_list = []
    sheet_name = next(iter(dict_data_types.keys()))
    attributes = sheet_name[:-1]+'_attributes'
    data_types = dict_data_types.pop(sheet_name)
    for config in product_config.values():
        config_dict = {attributes:{}}
        product_config_attributes = config_dict[attributes]
        for key, value in config.items():
            if "_id" in key:
                config_dict[key] = data_type_definition(sheet_name,key,value,data_types) #model.pop('outline')
                continue
            if isinstance(value,list):
                _sheet_name = list(dict_data_types)[0]
                _data_types = dict_data_types.get(_sheet_name)
                for v in value:
                    if isinstance(v,dict):
                        for _k,_v in v.items():
                            v[_k] = data_type_definition(_sheet_name,_k,_v,_data_types)
                product_config_attributes[key] = value
                continue
            if isinstance(value,dict):
                config_dict[key] = new_product_simple(value,dict_data_types)
                continue
            product_config_attributes[key] = data_type_definition(sheet_name,key,value,data_types)
        product_config_list.append(config_dict)

    return product_config_list

def error_message(sheet,column,type,value):
    return '''
### ERROR ###
Wrong type informed!
Sheet: {}
Column: {}
Informed type: {}
Cell contents: {}

    The type must be string, json, string_list or number and match cell contents
'''.format(sheet,column,type,value)

def error_message_header(header_length):
    return '''
### ERROR ###
Invalid header length: {}
Orientation: Insert a valid header length
'''.format(header_length)

def new_product_simple(product_simple,dict_data_types):
    product_simple_list = []
    sheet_name = list(dict_data_types)[-1]
    attributes = sheet_name+'_attributes'
    data_types = dict_data_types.get(sheet_name)
    for simple in product_simple.values():
        simple_dict = {attributes:{}}
        
        for key,value in simple.items():
            product_simple_attributes = simple_dict[attributes]
            if "_id" in key:
                simple_dict[key] = data_type_definition(sheet_name,key,value,data_types) #model.pop('outline')
                continue
            product_simple_attributes[key] = data_type_definition(sheet_name,key,value,data_types)
        product_simple_list.append(simple_dict)

    return product_simple_list

def validate_header(header_length):
    try:
        int(header_length)
    except:
        print(error_message_header(header_length))
        sys.exit(1)

def sheet_preprocessing(file, sheet, header_length=0):
    dict_index = {}
    df_dict = pd.read_excel(file, sheet_name=None)
        
    #removing unnamed and comment columns
    for sheet_name, sheet in df_dict.items():
        ignored = sheet.columns.str.startswith(('Unnamed:',"#"))
        cols = sheet.columns[~ignored]
        if sheet.columns[ignored].any():
            print("\nIgnoring columns in sheet {}:".format(sheet_name))
            print(", ".join(sheet.columns[ignored]))

        df_dict[sheet_name] = sheet[cols]

    dict_index = {}
    if(header_length):
        #save data type into dict
        for sheet_name,sheet in df_dict.items():
            dict_index[sheet_name] = data_type_dict(sheet)
            df_dict[sheet_name] = sheet.drop(0).reset_index(drop=True)
    else:
        for sheet_name in df_dict.keys():
            dict_index[sheet_name] = {}

    #removing 'nan' values and replacing with empty string ('')
    for sheet in df_dict.values():
        sheet.fillna('',inplace=True)

    df_dict = OrderedDict(df_dict)

    return df_dict,dict_index

def data_type_dict(df):
    columns = df.columns
    data_types = list(df.iloc[0])
    if (len(columns) == len(data_types)):
        return dict(zip(columns,data_types))
    else:
        print('Error in datatype rows')
        sys.exit(1)

#TODO: improve with argparse
file = sys.argv[1]
if len(sys.argv) > 2:
    parameter = sys.argv[2]
    params = parameter.split('=')
    if params[0] == '--header_rows':
        header_length = params[1]
        validate_header(header_length)
    else:
        print("Parameter not found. Parameter informed: ",params)
        sys.exit(1)    
else: 
    header_length = 0

print("\nReading file: ",file)
sheets = pd.ExcelFile(file)

print("\nReading sheets...")

print("\nFound sheets:")
print(", ".join(sheets.sheet_names))

dfs_dict,dict_data_types = sheet_preprocessing(file, sheets, header_length)

print("\nPreparing file...")
final_dict = prepare_product_dict(dfs_dict)
print("\nCreating JSON file...")
create_product_json(final_dict,dict_data_types)