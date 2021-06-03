import pandas as pd

def fill_dict(product_model_dict, list_sheets):
    for model in product_model_dict:
        product_config_dict = config_dict(model,list_sheets)

        product_config_dict = media_simple_dict(product_config_dict,list_sheets)
            
        product_model_dict[model]['product_config'] = product_config_dict

def config_dict(model_id,list_sheets):
    product_config = list_sheets[1].set_index('merchant_product_model_id').loc[model_id]
    product_config_dict = product_config.set_index('merchant_product_config_id').to_dict(orient='index')
    return product_config_dict

def media_simple_dict(product_config_dict,list_sheets):
    media_df, product_simple_df = set_index('merchant_product_config_id',list_sheets)
    
    for config in product_config_dict:
        df = media_df.loc[config]
        media_dict = df[df.columns[2:]].to_dict(orient='records')
        
        df = product_simple_df.loc[config]
        product_simple_dict = df.set_index('merchant_product_simple_id').to_dict(orient='index')
        
        product_config_dict[config]['media'] = media_dict
        product_config_dict[config]['product_simple'] = product_simple_dict

    return product_config_dict


def set_index(index_name,list_sheets):
    return [list_sheets[2].set_index([index_name]),list_sheets[3].set_index([index_name])]

sheets = pd.ExcelFile("./shoe.xlsx")

list_sheets = []
for sheet in sheets.sheet_names:
    list_sheets.append(pd.read_excel("./shoe.xlsx",sheet_name=sheet))

product_model_dict = list_sheets[0].set_index('merchant_product_model_id').to_dict(orient='index')

final_dict = fill_dict(product_model_dict,list_sheets)
