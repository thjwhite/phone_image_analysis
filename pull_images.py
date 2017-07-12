import os
import sys
import json
import uuid
import hashlib
import time
import traceback

from urllib.parse import urlparse

import lmdb
import requests


GOOGLE_SEARCH_URL = 'https://www.googleapis.com/customsearch/v1'
GOOGLE_API_OUTPUT_DIR = '.google_api_queries'
IMAGE_REPO_DIR = '.images'
LMDB_FILE = '.registrar'
IOS_CLASS = 'ios'
ANDROID_CLASS = 'android'
IOS_SEARCH_TERMS = ['iphone', 'iphone 7', 'iphone 6', 'ios screenshot', 'ipad']
ANDROID_SEARCH_TERMS = ['android phone', 'android screenshot',
                        'samsung galaxy', 'google pixel', 'android tablet']


def grab_auth():
    """
    grab some auth tokens from environment
    """
    custom_search_engine_id = os.environ.get('GOOGLE_API_CX')
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    return custom_search_engine_id, google_api_key


def generate_iphone_search_params(term, engine_id, api_key, start=1):
    """
    parameters for a search for phone images
    """
    params = dict()
    params['cx'] = engine_id  # custom search engine identifier
    params['key'] = api_key  # api key
    params['searchType'] = 'image'  # tell google we want images, not links
    params['q'] = term  # our search term
    params['start'] = start  # pagination start
    return params


def execute_request(term, custom_search_engine_id, google_api_key, start=1):
    """
    execute request to google for the results
    """
    params = generate_iphone_search_params(term, custom_search_engine_id, google_api_key, start)
    response = requests.get(GOOGLE_SEARCH_URL, params=params)
    print(response)
    if response.status_code != 200:
        print(params)
        print(response.content)
        raise ValueError('could not successfully query google')
    payload = response.json()
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


def write_new(url, content, classification, hash_val, lmdb_env):
    """
    writes out a new image
    """
    uuid_val = uuid.uuid4()
    with open('%s/%s/%s' % (IMAGE_REPO_DIR, classification, uuid_val), 'wb') as image_file:
        image_file.write(content)
    print('wrote url=%s\n      uuid=%s\n      sha256=%s\n' %
          (url, str(uuid_val), hash_val.hexdigest()))
    with lmdb_env.begin(write=True) as txn:
        # map our hash value to the image uuid
        txn.put(hash_val.digest(), uuid_val.bytes)


def dedup(hash_val, lmdb_env):
    """
    returns whether of not this hash is already in our image repository
    """
    with lmdb_env.begin() as txn:
        image_uuid = txn.get(hash_val.digest())
        return image_uuid is not None


def process_urls(urls, classification, lmdb_env):
    """
    urls is a list of tuples (url, thumbnail). We try the url first,
    but if it fails to download it we can use the thumbnail.
    takes each url in the list downloads it and then processes what to do with it.
    """
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
            hash_val = hashlib.sha256(content)
            if not dedup(hash_val, lmdb_env):
                write_new(url, content, classification, hash_val, lmdb_env)
            else:
                print('Duplicate image detected')
        except requests.exceptions.RequestException:
            print('ERROR')
            print(traceback.format_exc())


def process_term(term, classification, custom_search_engine_id, google_api_key, lmdb_env):
    """
    for a particular term go out to google, and then download the images
    """
    start = 1
    while start < 100:
        payload = execute_request(term, custom_search_engine_id, google_api_key, start=start)
        t_process = time.time()
        print('%s\n' % t_process)
        with open('%s/%s' % (GOOGLE_API_OUTPUT_DIR, t_process), 'w') as search_res_file:
            json.dump(payload, search_res_file)

        # process_payload(payload)
        urls = get_urls(payload)
        process_urls(urls, classification, lmdb_env)

        start = payload['queries']['nextPage'][0]['startIndex']


def main():
    """
    main entry point into the program,
    drives the process of going to google, downloading the images, etc.
    """
    custom_search_engine_id, google_api_key = grab_auth()
    if custom_search_engine_id is None or google_api_key is None:
        print('please provide CSE ID and API Key via ' +
              'environment variables (GOOGLE_API_CX and GOOGLE_API_KEY)')
        sys.exit(1)

    if not os.path.exists(GOOGLE_API_OUTPUT_DIR):
        os.makedirs(GOOGLE_API_OUTPUT_DIR)
    if not os.path.exists(IMAGE_REPO_DIR):
        os.makedirs(IMAGE_REPO_DIR)
    if not os.path.exists('%s/%s' % (IMAGE_REPO_DIR, IOS_CLASS)):
        os.makedirs('%s/%s' % (IMAGE_REPO_DIR, IOS_CLASS))
    if not os.path.exists('%s/%s' % (IMAGE_REPO_DIR, ANDROID_CLASS)):
        os.makedirs('%s/%s' % (IMAGE_REPO_DIR, ANDROID_CLASS))

    lmdb_env = lmdb.open(LMDB_FILE, max_dbs=1, map_size=(1000 * 1000 * 1000))

    for term in IOS_SEARCH_TERMS:
        process_term(term, IOS_CLASS, custom_search_engine_id, google_api_key, lmdb_env)

    for term in ANDROID_SEARCH_TERMS:
        process_term(term, ANDROID_CLASS, custom_search_engine_id, google_api_key, lmdb_env)

if __name__ == "__main__":
    main()
