"""
# todo - make multiple queries to get around 10 page limit (iphone 6 vs iphone 7)
# todo - pylint
"""
import requests
import os
import sys
import json
import uuid
import hashlib
import time
import traceback
import lmdb
from urllib.parse import urlparse

GOOGLE_SEARCH_URL='https://www.googleapis.com/customsearch/v1'
DEBUG=False
WRITE_RESPONSE=False

DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR='.sample_google_output'
GOOGLE_API_OUTPUT_DIR='.google_api_queries'
IMAGE_REPO_DIR='.images'

LMDB_FILE='.registrar'


def grab_auth():
    """
    grab some auth tokens from environment
    """
    custom_search_engine_id = os.environ.get('GOOGLE_API_CX')
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    return custom_search_engine_id, google_api_key


def generate_iphone_search_params(cx, api_key, start=1):
    """
    parameters for a search for iphones
    """
    params = dict()
    params['cx'] = cx  # custom search engine identifier
    params['key'] = api_key  # api key
    params['searchType'] = 'image'  # tell google we want images, not links
    params['q'] = 'iphone'  # our search term
    params['start'] = start  # pagination start
    return params


def execute_request(custom_search_engine_id, google_api_key, start=1):
    """
    execute request or load debug payload, save output in special location if enabled
    """
    if DEBUG:
        with open(DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR) as f:
            payload = json.load(f)
    else:
        params = generate_iphone_search_params(custom_search_engine_id, google_api_key, start)
        response = requests.get(GOOGLE_SEARCH_URL, params=params)
        print(response)
        if response.status_code != 200:
            print(params)
            print(response.content)
            raise ValueError('could not successfully query google')
        payload = response.json()
        if WRITE_RESPONSE:
            with open(DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR, 'w+') as f:
                json.dump(payload, f)
    return payload


def get_urls(payload):
    """
    parse payload to get list of urls. returns a list of tuples (url, thumbnail)
    so we have backup images if a link does not work.
    """
    urls = list()
    for result in payload['items']:
        link = result['link']
        thumbnail = result['image']['thumbnailLink']  # grab the thumbnail as backup
        urls.append((link, thumbnail))
    return urls


def write_new(url, content, h, lmdb_env):
    """
    writes out a new image
    """
    u = uuid.uuid4()
    with open('%s/%s' % (IMAGE_REPO_DIR, u), 'wb') as f:
        f.write(content)
    print('wrote url=%s\n      uuid=%s\n      sha256=%s\n' % (url, str(u), h.hexdigest()))
    with lmdb_env.begin(write=True) as txn:
        # map our hash value to the image uuid
        txn.put(h.digest(), u.bytesq)


def dedup(h, lmdb_env):
    with lmdb_env.begin() as txn:
        image_uuid = txn.get(h.digest())
        return image_uuid is not None


def process_urls(urls, lmdb_env):
    for (url, thumb) in urls:
        try:
            url = urlparse(url, scheme='http').geturl()
            img_resp = requests.get(url)
            if img_resp.status_code != 200:
                url = urlparse(thumb, scheme='http').geturl()
                img_resp = requests.get(url)
                if img_resp.status_code != 200:
                    raise ValueError('failure to grab both image and thumbnail')
            content = img_resp.content
        except:
            print('ERROR')
            print(traceback.format_exc())
        h = hashlib.sha256(content)
        if not dedup(h, lmdb_env):
            write_new(url, content, h, lmdb_env)
        else:
            print('Duplicate image detected')


def main():
    custom_search_engine_id, google_api_key = grab_auth()    
    if custom_search_engine_id is None or google_api_key is None:
        print('please provide CSE ID and API Key via environment variables (GOOGLE_API_CX and GOOGLE_API_KEY)')
        sys.exit(1)
    if not os.path.exists(GOOGLE_API_OUTPUT_DIR):
        os.makedirs(GOOGLE_API_OUTPUT_DIR)
    if not os.path.exists(IMAGE_REPO_DIR):
        os.makedirs(IMAGE_REPO_DIR)

    lmdb_env = lmdb.open(LMDB_FILE, max_dbs=1, map_size=(1000 * 1000 * 1000))

    start = 1
    while True:
        payload = execute_request(custom_search_engine_id, google_api_key, start=start)
        t_process = time.time()
        print('%s\n' % t_process)
        with open ('%s/%s' % (GOOGLE_API_OUTPUT_DIR, t_process), 'w') as f:
            json.dump(payload, f)

        # process_payload(payload)
        urls = get_urls(payload)
        process_urls(urls, lmdb_env)

        start = payload['queries']['nextPage'][0]['startIndex']


if __name__ == "__main__":
    main()
