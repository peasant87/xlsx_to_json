#!/usr/bin/env python3

import sys
import os
import pandas as pd
import ast
import json

MODEL_ID = 'merchant_product_model_id'
CONFIG_ID = 'merchant_product_config_id'
SIMPLE_ID = 'merchant_product_simple_id'

def prepare_product_dict(product_model_dict, list_sheets):
    for model in product_model_dict:
        product_config_dict = prepare_config_dict(model,list_sheets)

        product_config_dict = prepare_media_simple_dict(product_config_dict,list_sheets)
            
        product_model_dict[model]['product_config'] = product_config_dict
    return product_model_dict

def prepare_config_dict(model_id,list_sheets):
    product_config = list_sheets[1].set_index(MODEL_ID).loc[model_id]
    product_config_dict = product_config.set_index(CONFIG_ID).to_dict(orient='index')
    return product_config_dict

def prepare_media_simple_dict(product_config_dict,list_sheets):
    media_df, product_simple_df = set_index(CONFIG_ID,list_sheets)
    
    for config in product_config_dict:
        df = media_df.loc[config]
        media_dict = df[df.columns[2:]].to_dict(orient='records')
        
        df = product_simple_df.loc[config]
        product_simple_dict = df.set_index(SIMPLE_ID).to_dict(orient='index')
        
        product_config_dict[config]['media'] = media_dict
        product_config_dict[config]['product_simple'] = product_simple_dict

    return product_config_dict


def set_index(index_name,list_sheets):
    return [list_sheets[2].set_index([index_name]),list_sheets[3].set_index([index_name])]

def create_product_json(products_dicts):
    for product_id in products_dicts:
        product_dict = {'outline':'','product_model':{}}
        model = products_dicts[product_id]
        product_dict['outline'] = model.pop('outline')
        product_config = model.pop('product_config')
        
        product_model = product_dict['product_model']
        product_model[MODEL_ID] = product_id
        
        product_model_attributes = {}
        product_model_attributes['name'] = model.get('name')
        product_model_attributes['brand_code'] = model.get('brand_code')
        product_model_attributes['size_group'] = {'size':model.get('size_group')}
        product_model_attributes['target_genders'] = [model.get('target_genders')]
        product_model_attributes['target_age_groups'] = [model.get('target_age_groups')]
        product_model['product_model_attributes'] = product_model_attributes
            
        product_model['product_configs'] = new_product_config(product_config)
        save_json(product_dict,product_id)
        
def save_json(product_dict,id):
    filename = "./output_json/{}_{}.json".format(product_dict['outline'],id)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as outfile:
        json.dump(product_dict, outfile, indent=4)
    print("Saved JSON file at: ",filename)

def new_product_config(product_config):
    product_config_list = []
    for key in product_config:
        config = product_config[key]
        new_product_config = {}
        new_product_config[CONFIG_ID] = key
        
        product_config_attributes = {}
        product_config_attributes['color_code.primary'] = config.get('color_code.primary')
        try:
            product_config_attributes['description'] = ast.literal_eval(config.get('description'))
        except: 
            print("Bad formed JSON field: ",'description')

        product_config_attributes['supplier_color'] = config.get('supplier_color')
        product_config_attributes['fabric_definition'] = [config.get('fabric_definition')]
        
        try:
            product_config_attributes['material.upper_material_clothing'] = \
                list(ast.literal_eval(config.get('material.upper_material_clothing')))
        except: 
            print("Bad formed JSON field: ",'material.upper_material_clothing')

        try:
            product_config_attributes['material.futter_clothing'] = \
                list(ast.literal_eval(config.get('material.futter_clothing')))
        except: 
            print("Bad formed JSON field: ",'material.futter_clothing')

        try:
            product_config_attributes['material.upper_material_top'] = \
                list(ast.literal_eval(config.get('material.upper_material_top')))
        except: 
            print("Bad formed JSON field: ",'material.upper_material_top')

        product_config_attributes['media'] = config.get('media')
        product_config_attributes['season_code'] = config.get('season_code')
        product_config_attributes['breathable'] = [config.get('breathable')]
        product_config_attributes['assortment_type'] = [config.get('assortment_type')]
        product_config_attributes['occasion'] = [config.get('occasion')]
        product_config_attributes['condition'] = config.get('condition')
        product_config_attributes['sport_type'] = [config.get('sport_type')]
        product_config_attributes['waterproof'] = [config.get('waterproof')]
        product_config_attributes['washing_instructions'] = [config.get('washing_instructions')]
        new_product_config['product_config_attributes'] = product_config_attributes
        
        product_simple = config.pop('product_simple')
    
        new_product_config['product_simples'] = new_product_simple(product_simple)   
        product_config_list.append(new_product_config)
    return product_config_list

def new_product_simple(product_simple):
    product_simple_list = []
    for ps in product_simple:
        simple = product_simple[ps]
        new_product_simple = {}
        new_product_simple[SIMPLE_ID] = ps
        
        product_simple_attributes = {}
        product_simple_attributes['ean'] = str(simple.get('ean'))
        product_simple_attributes['size_codes'] = {'size':simple.get('size_codes')}
        
        new_product_simple['product_simple_attributes'] = product_simple_attributes
        product_simple_list.append(new_product_simple)
    return product_simple_list

file = sys.argv[1]

print("Reading file: ",file)
sheets = pd.ExcelFile(file)

list_sheets = []
print("Reading sheets...")
for sheet in sheets.sheet_names:
    print("Found sheet: ",sheet)
    list_sheets.append(pd.read_excel(file,sheet_name=sheet))

product_model_dict = list_sheets[0].set_index(MODEL_ID).to_dict(orient='index')
print("Preparing file...")
final_dict = prepare_product_dict(product_model_dict,list_sheets)
print("Creating JSON file...")
create_product_json(final_dict)