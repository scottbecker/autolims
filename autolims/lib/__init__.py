import os
import math
import requests
import json
import logging.config

def setup_logging(
    default_path='logging.json', 
    default_level=logging.INFO,
    env_key='LOG_CFG'):  
    """Setup logging configuration

    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
        
        
        
def lists_intersect(list1, list2):
    return len(set(list1).intersection(set(list2)))


def get_dict_optional_value(d,keys_to_try_in_order, default_value=None):
    """
    Tries each key in order, if not value is found, returns default_value
    """
    
    for key in keys_to_try_in_order:
        if key in d and d.get(key):
            return d[key]
        
    return default_value


def round_up(x,nearest_number=1):
    nearest_number = nearest_number * 1.0
    return int(math.ceil(x / nearest_number)) * nearest_number


IDT_COOKIE = None

def get_melting_temp(dna_sequence, oligo_concentration_uM,
                     pcr_settings='q5'):
    global IDT_COOKIE
    
    #@TODO: update this to use http://tmcalculator.neb.com/#!/ since its probably accounting for the salt concentration in the buffer
    
    if not IDT_COOKIE:
        r = requests.get('http://www.idtdna.com/calc/analyzer',allow_redirects=False)
        IDT_COOKIE = r.cookies['ASP.NET_SessionId']       
        
    headers = {"content-type":'application/json','Cookie':'ASP.NET_SessionId=%s'%IDT_COOKIE}
    
    idt_response = requests.post('https://www.idtdna.com/calc/analyzer/home/analyze',json={
        "settings": {
            "Sequence": dna_sequence,
            "NaConc": 0,
            "MgConc": 2,
            "DNTPsConc": 5, 
            "OligoConc": oligo_concentration_uM,
            "NucleotideType": "DNA"
        }
    }, verify=False
    ,headers=headers)    
    
    idt_response.raise_for_status()
    
    return idt_response.json()['MeltTemp']
    
    


