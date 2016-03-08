#! /usr/bin/env python3
"""
create, read, update, delete with libcli
"""
import json
from pprint import pprint

from libcli import default, command, error, run
import libcli.opttools

SOME_FILE = 'crud.log'
data = None

try:
    with open(SOME_FILE, 'r') as f:
        data = json.load(f)
except (OSError, json.JSONDecodeError):
    data = {}

def write_to_disk(data):
    try:
        with open(SOME_FILE, 'w') as f:
            data = json.dump(data, f)
        print('written.')
    except (OSError):
        print('Failed to write')

@error
class KeyExisted(Exception):
    pass

@error
class KeyNotExist(Exception):
    pass

@command
def create(key, value):
    if key in data:
        raise KeyExisted()
    else:
        data[key] = value
    write_to_disk(data)

@command
def read(key):
    if key in data:
        print(data[key])
    else:
        raise KeyNotExist()

@command
def update(key, value):
    if key in data:
        data[key] = value
    else:
        raise KeyNotExist()
    write_to_disk(data)

@command
def delete(key):
    if key in data:
        del data[key]
    else:
        raise KeyNotExist()
    write_to_disk(data)

@command(_name='list')
def _list():
    pprint(data)

if __name__ == '__main__':
    run()
