import requests
import os
import sys
import json
import uuid
import hashlib
import time
from urllib.parse import urlparse

GOOGLE_SEARCH_URL='https://www.googleapis.com/customsearch/v1'
DEBUG=False
WRITE_RESPONSE=False

DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR='.sample_google_output'
GOOGLE_API_OUTPUT_DIR='.google_api_queries'
IMAGE_REPO_DIR='.images'

def grab_auth():
    # grab some auth tokens from environment
    custom_search_engine_id = os.environ.get('GOOGLE_API_CX')
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    return custom_search_engine_id, google_api_key


def generate_iphone_search_params(cx, api_key, start=1):
    # search for iphones
    params = dict()
    params['cx'] = cx
    params['key'] = api_key
    params['q'] = 'iphone'
    params['imgType'] = 'photo'
    params['start'] = start
    return params


def execute_request(custom_search_engine_id, google_api_key, start=1):
    if DEBUG:
        with open(DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR) as f:
            payload = json.load(f)
    else:
        params = generate_iphone_search_params(custom_search_engine_id, google_api_key, start)
        response = requests.get(GOOGLE_SEARCH_URL, params=params)
        print(response)
        payload = response.json()
        if WRITE_RESPONSE:
            with open(DEBUG_SAMPLE_GOOGLE_API_OUTPUT_DIR, 'w+') as f:
                json.dump(payload, f)
    return payload


def process_payload(payload):
    for search_item in payload['items']:
        print(search_item['link'])
        urls = list()
        if 'pagemap' in search_item and 'imageobject' in search_item['pagemap']:
            imgs = search_item['pagemap']['imageobject']
            for img in imgs:
                if 'url' in img:
                    urls.append(img['url'])
                elif 'contenturl' in img:
                    urls.append(img['contenturl'])
                elif 'image' in img:
                    urls.append(img['image'])
                else:
                    print('no images! probably missed something')

        if len(urls) == 0:
            continue
        
        for url in urls:
            url = urlparse(url, scheme='http').geturl()
            img_resp = requests.get(url)
            content = img_resp.content
            h = hashlib.sha256(content).hexdigest()
            u = str(uuid.uuid4())
            with open('%s/%s' % (IMAGE_REPO_DIR, u), 'wb') as f:
                f.write(img_resp.content)
            print('wrote uuid=%s sha256=%s' % (u, h))
        print()


def main():
    custom_search_engine_id, google_api_key = grab_auth()    
    if custom_search_engine_id is None or google_api_key is None:
        print('please provide CSE ID and API Key via environment variables (GOOGLE_API_CX and GOOGLE_API_KEY)')
        sys.exit(1)

    payload = execute_request(custom_search_engine_id, google_api_key)

    if not os.path.exists(GOOGLE_API_OUTPUT_DIR):
        os.makedirs(GOOGLE_API_OUTPUT_DIR)
    if not os.path.exists(IMAGE_REPO_DIR):
        os.makedirs(IMAGE_REPO_DIR)
    t_process = time.time()
    print('%s\n' % t_process)
    with open ('%s/%s' % (GOOGLE_API_OUTPUT_DIR, t_process), 'w') as f:
        json.dump(payload, f)

    process_payload(payload)


if __name__ == "__main__":
    main()
