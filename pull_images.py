import requests
import os
import sys
import json
import uuid
import hashlib
import time

GOOGLE_SEARCH_URL='https://www.googleapis.com/customsearch/v1'
DEBUG=True
WRITE_RESPONSE=False

def main():
    custom_search_engine_id = os.environ.get('GOOGLE_API_CX')
    google_api_key = os.environ.get('GOOGLE_API_KEY')

    if custom_search_engine_id is None or google_api_key is None:
        print('please provide CSE ID and API Key via environment variables')
        sys.exit(1)

    params = dict()
    params['cx'] = custom_search_engine_id
    params['key'] = google_api_key
    params['q'] = 'iphone'
    params['imgType'] = 'photo'

    if DEBUG:
        with open('.sample_google_output') as f:
            payload = json.load(f)
    else:
        response = requests.get(GOOGLE_SEARCH_URL, params=params)
        print(response)
        payload = response.json()
        if WRITE_RESPONSE:
            with open('.sample_google_output', 'w+') as f:
                json.dump(payload, f)

    if not os.path.exists('.google_api_queries'):
        os.makedirs('.google_api_queries')
    if not os.path.exists('.images'):
        os.makedirs('.images')
    t_process = time.time()
    print('====================')
    print(t_process)
    print('====================')
    with open ('.google_api_queries/%s' % t_process, 'w') as f:
        json.dump(payload, f)
    
    for search_item in payload['items']:
        print('=================================')
        print(search_item['link'])
        urls = list()
        if 'pagemap' in search_item and 'imageobject' in search_item['pagemap']:
            imgs = search_item['pagemap']['imageobject']
            for img in imgs:
                if 'url' in img:
                    urls.append(img['url'])
                elif 'contenturl' in img:
                    urls.append(img['contenturl'])
                else:
                    print('no images! probably missed something')

        if len(urls) == 0:
            continue
        
        print('downloading images')
        for url in urls:
            img_resp = requests.get(url)
            content = img_resp.content
            h = hashlib.sha256(content).hexdigest()
            u = str(uuid.uuid4())
            with open('.images/%s' % u, 'wb') as f:
                f.write(img_resp.content)
            print('wrote uuid=%s sha256=%s' % (u, h))
            
    

if __name__ == "__main__":
    main()
