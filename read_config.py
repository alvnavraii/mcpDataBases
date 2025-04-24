import json
import os


dict_configs = {}

def read_config(file_path):
    dict_config = {}
    for file in file_path:
        with open(file, "r") as f:
            dict_aux = json.load(f)
            dict_aux = dict_aux["mcpServers"]
            for key in dict_aux.keys():
                if key not in dict_config:
                    dict_config[key] = dict_aux[key]["args"]
    return dict_config

