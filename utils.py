#!/usr/bin/env python

import json
import yaml
import xmltodict
from datetime import datetime
from pathlib import Path
import os
#data_folder = '../data/'
DATA_DIR = Path('./data')
def load_config(filename):
    """Load configuration from a yaml file"""
    with open(filename) as f:
        return yaml.safe_load(f)


def save_config(config, filename):
    """Save configuration to a yaml file"""
    with open(filename, "w+") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def pretty_print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

def save_json_to_file(data, filename):
    if not DATA_DIR.is_dir():
        os.mkdir(DATA_DIR)
    with open(filename, 'w') as outfile:
        outfile.write(json.dumps(data, indent=4))

def polar_datetime_to_python_datetime_str(polar_dt):
    new_dt = polar_dt.replace('T', ' ')
    try:
        date_time_obj = datetime.strptime(new_dt, '%Y-%m-%d %H:%M:%S.%f')
    except:
        date_time_obj = datetime.strptime(new_dt, '%Y-%m-%d %H:%M:%S')
    
    return date_time_obj.strftime('%Y-%m-%d+%H_%M_%S_%f')

def xml_to_dict(xml_object):
    data_dict = xmltodict.parse(xml_object)

    return data_dict