import json
import os
import subprocess

model_dir = os.path.join('models/')

with open('model_urls.json', 'r') as f:
    urls_json = json.load(f)

    url_list = []

    for row in urls_json:
        url_list.append(urls_json[row])

    # ok, now download them

    # create download folder
    # os.mkdir(model_dir)

    for urls in url_list:
        # go in reverse order because table sometimes has most recent version last
        found = False
        print(urls, len(urls))
        urls.reverse()  # do most recent (last) version first
        for url in urls:
            print('downloading:', url)
            subprocess.Popen(args=['wget -nc -P {0} {1}'.format(model_dir, url)], shell=True)