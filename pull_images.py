import requests
import os
import sys
import json

GOOGLE_SEARCH_URL='https://www.googleapis.com/customsearch/v1'
DEBUG=False
WRITE_RESPONSE=True

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
    
    for search_item in payload['items']:
        print('=================================')
        print(search_item['link'])
        # todo - null check
        print([img['url'] for img in search_item['pagemap']['imageobject']])
        
    

if __name__ == "__main__":
    main()
