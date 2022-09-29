import logging
import logging.handlers
import os
import time

import requests
from frameioclient import FrameioClient

settings = {
'API_ENDPOINT' : "https://florc4u1li.execute-api.us-east-1.amazonaws.com/autoDownloadAPI" ,
'POLL_RATE' : 2 ,
'DESTINATION' : "~/fioDownload" ,
'LOG_PATH' : '~/.fio/logs/auto_download.log' ,
'SKIP_EXISTING' : True ,
'PROJECT_ID' : "a46ef2de-475a-4a60-a135-cc309df01ef4" ,
'PATH_FILTER' : ".RDC" #Includes in filepath
}
print(settings)
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

print("POLLING FOR NEW EVENTS...")
while True:
    
    ####################################################
    ### Set up Variables
    #token = os.environ.get('FRAMEIO_AUTH_TOKEN')
    #client = FrameioClient(token)

    ####################################################
    ### Poll API endpoint
    params = {
        #'token' : token ,
        'project_id' : settings['PROJECT_ID']
    }
    response = requests.get(settings['API_ENDPOINT'], params=params)

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
                print(f'SKIPPING EXISTING FILE: {download_path}')
                continue
            else:
                os.remove(download_path)

        ####################################################
        ### Download file
        client = FrameioClient(token)
        download = client.assets.download(asset_blob , download_dir)
        #download = client.assets._download(assetID , download_dir)

        #obj = SmartDL(download_url, download_path)
        #obj.start()
        
        #os.system(f'curl "{download_url}" -o "{download_path}"')

    time.sleep(settings['POLL_RATE'])

