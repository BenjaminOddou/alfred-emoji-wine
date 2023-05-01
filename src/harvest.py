import json
from utils import api

data = api()
items = []

if data:
    num_object = len(data['items'])
    items = [
        {
            'title': 'Refresh the API',
            'subtitle': 'Press ⏎ to grab emoji data from unicode.org',
            'arg': '_api',
            'icon': {
                'path': 'icons/sync.webp',
            },
        },
        {
            'title': 'API information',
            'subtitle': f'Last update : {data["info"]["time"]} ǀ {num_object} Emojis ǀ {data["info"]["lang"]["title"]}',
            'valid': False,
            'icon': {
                'path': 'icons/info.webp',
            },
        }
    ]
else:
    items.append({
        'title': 'No API detected',
        'subtitle': 'Press ⏎ to grab emoji data from unicode.org',
        'arg': '_api',
        'icon': {
            'path': 'icons/info.webp',
        },
    })


print(json.dumps({'items': items}))