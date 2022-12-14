import json
import logging
import logging.handlers
import os
import sys
import time
from pprint import pformat

import requests
from frameioclient import FrameioClient

######################################################
### GET DOWNLOAD SETTINGS

SETTINGS_PATH = os.path.expanduser("~/.fio/autoDownloadSettings.json")

default_settings = {
'API_ENDPOINT' : "https://florc4u1li.execute-api.us-east-1.amazonaws.com/autoDownloadAPI" ,
'POLL_RATE' : 2 ,
'DESTINATION' : "~/fioDownload" ,
'LOG_PATH' : '~/.fio/logs/auto_download.log' ,
'SKIP_EXISTING' : True ,
'PROJECT_ID' : "a46ef2de-475a-4a60-a135-cc309df01ef4" ,
'PATH_FILTER' : ".RDC"
}

if os.path.isfile(SETTINGS_PATH):
    with open(SETTINGS_PATH, "r") as f:
        settings = json.load(f)
        settings['SETTINGS_PATH'] = SETTINGS_PATH
else:
    with open(SETTINGS_PATH, "w") as f:
        f.write(json.dumps(default_settings))
    settings = default_settings
    settings['SETTINGS_PATH'] = SETTINGS_PATH

if not settings.get('PROJECT_ID'):
    print('ERROR: NO PEOJECT ID PROVIDED')
    sys.exit()
######################################################

######################################################
### SETUP LOGGING
# create logger with 'application'
log = logging.getLogger('main')
log.propagate = False
log.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
logpath = os.path.expanduser(settings['LOG_PATH'])
if not os.path.exists(os.path.dirname(logpath)):
    os.makedirs(os.path.dirname(logpath))
fh = logging.handlers.RotatingFileHandler(logpath, maxBytes=1024*1024*500, backupCount=3)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(module)16s - %(levelname)s - %(message)s',
                                "%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)
######################################################

log.info(pformat(settings))

log.info("POLLING FOR NEW EVENTS...")
while True:

    ####################################################
    ### Poll API endpoint
    params = {
        #'token' : token ,
        'project_id' : settings['PROJECT_ID']
    }
    try:
        response = requests.get(settings['API_ENDPOINT'], params=params)
    except Exception as e:
        log.error(f"ERROR on API request: {e}")

    ####################################################
    ### Validate Reponse

    if response.status_code == 200:
        messages = response.json()
    else:
        time.sleep(settings['POLL_RATE'])
        continue

    if not messages:
        time.sleep(settings['POLL_RATE'])
        continue

    ####################################################
    ### Get asset info

    for message in messages:
        assetID = message['asset_id']
        #assetName = message['filename']
        filepath = message['filepath']
        #download_url = message['download_url']
        token = message['token']
        asset_blob = message['asset_blob']

        if not settings['PATH_FILTER'] in filepath:
            continue
        ####################################################
        ### Check if exists

        download_path = os.path.expanduser(os.path.join(settings['DESTINATION'], filepath[1:]))
        download_dir = os.path.dirname(download_path)

        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        if os.path.isfile(download_path):
            if settings['SKIP_EXISTING']:
                log.info(f'SKIPPING EXISTING FILE: {download_path}')
                continue
            else:
                os.remove(download_path)

        ####################################################
        ### Download file
        client = FrameioClient(token)
        try:
            download = client.assets.download(asset_blob , download_dir)
        except Exception as e:
            log.error(f'ERROR ON DOWNLOAD: {e}')

    time.sleep(settings['POLL_RATE'])


