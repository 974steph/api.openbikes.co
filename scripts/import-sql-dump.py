'''
'''

import os
import argparse
import time
import subprocess

from pymongo import MongoClient
from tqdm import tqdm

import util


START_TIME = time.time()

POSTGRES_PORT = os.environ.get('POSTGRES_PORT')


def create_remote_connexion(port=5432):
    # Create a SSH tunnel in the background
    tunnel_command = 'ssh -f -N -L {}:localhost:5432 46.101.234.224 -l max'.format(
        port)
    try:
        subprocess.call(tunnel_command, shell=True)
    except Exception:
        print('Port {} is already in use'.format(port))
    return MongoClient(port=port)


def fetch(city_name, local, remote):
    util.notify('Fetching...', 'green', START_TIME)
    # Check if there already is some data in the local database
    if local.find().count() != 0:
        # Get the most recent date in the local database
        max_date = local.find_one(sort=[('_id', -1)])['_id']
        # Delete the latest document to avoid incomplete data
        local.delete_one({'_id': max_date})
        util.notify('Will only import data for {0} after {1} (included)'.format(
            city_name, max_date), 'yellow', START_TIME)
        # Query the relevant data on the remove server
        cursor = remote.find({'_id': {'$gte': max_date}}, sort=[('_id', 1)])
    else:
        util.notify('Importing all data for {} (this could take a while)'.format(
            city_name), 'yellow', START_TIME)
        # Query the relevant data on the remove server
        cursor = remote.find(sort=[('_id', 1)])

    total = cursor.count()
    util.notify('Found {0} document(s)'.format(total), 'cyan', START_TIME)
    # Insert it locally
    for i, cur in tqdm(enumerate(cursor)):
        local.insert(cur)
    util.notify('Done', 'green')


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument('city', type=str, help='City for which to import data')
    PARAMS = PARSER.parse_args()
    CITY_NAME = PARAMS.city

    util.notify('Attempting to retrieve data for {}'.format(
        CITY_NAME), 'green', START_TIME)

    # Define the remote and the local connections
    REMOTE_CONN = create_remote_connexion(POSTGRES_PORT)
    LOCAL_CONN = MongoClient()

    # Define the different collections
    C = {
        'local': {
            'ts': LOCAL_CONN.OpenBikes[CITY_NAME],
            'weather': LOCAL_CONN.OpenBikes_Weather[CITY_NAME]
        },
        'remote': {
            'ts': REMOTE_CONN.OpenBikes[CITY_NAME],
            'weather': REMOTE_CONN.OpenBikes_Weather[CITY_NAME]
        }
    }

    util.notify('Established connection to the remote database',
                'green', START_TIME)

    util.notify('Begun retrieving bike station updates', 'green', START_TIME)
    fetch(CITY_NAME, C['local']['ts'], C['remote']['ts'])
    util.notify('Finished retrieving bike station updates',
                'green', START_TIME)

    util.notify('Begun retrieving weather updates', 'green', START_TIME)
    fetch(CITY_NAME, C['local']['weather'], C['remote']['weather'])
    util.notify('Finished retrieving weather updates', 'green', START_TIME)
