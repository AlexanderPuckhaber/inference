import json
import urlextract

# from: https://stackoverflow.com/questions/66185838/python-convert-markdown-table-to-json-with
def mrkd2json(inp):
    lines = inp.split('\n')
    ret=[]
    keys=[]
    for i,l in enumerate(lines):
        if i==0:
            keys=[_i.strip() for _i in l.split('|')]
        elif i==1: continue
        else:
            ret.append({keys[_i]:v.strip() for _i,v in enumerate(l.split('|')) if  _i>0 and _i<len(keys)-1})
    # return json.dumps(ret, indent = 4)
    return ret

with open('README.md') as f:
    text = f.read()

    # parse text for table

    text_before_table = '## Supported Models\n\n'
    text_after_table = '\n\n## Disclaimer'

    table_and_after = text.split(text_before_table)[1]
    only_table = table_and_after.split(text_after_table)[0]

    # print(only_table)

    table_json = mrkd2json(only_table)
    # print(table_json)

    ue = urlextract.URLExtract()

    url_dict = {}

    i = 0
    for row in table_json:
        urls = ue.find_urls(text=row['model link'])
        url_dict[i] = urls
        i += 1

    with open('model_urls.json', 'w') as ff:
        json.dump(url_dict, ff)
