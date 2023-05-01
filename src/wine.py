import json
from utils import api, icons_folder_path, language

data = api()
items = []

if data:
    with open('json/lang.json') as file:
        langs = json.load(file)
    for item in langs:
        if item["value"] == language:
            lang = item["title"]
            break
    if language != data['info']['lang']['value']:
        items.append({
            'title': 'Refresh the API',
            'subtitle': f'Press ⏎ to grab emoji data using with language : {lang}',
            'arg': '_api',
            'icon': {
                'path': 'icons/info.webp',
            },
            'mods': {
                'cmd': {
                    'subtitle': f'Press ⏎ to grab emoji data using with language : {lang}',
                    'valid': False
                }
            },
        })
    else:
        for item in data['items']:
            name, emoji, title, keywords = item.get('name'), item.get('emoji'), item.get('title'), item.get('keywords')
            second_name = name.replace(" ", "_").replace(":", "").lower()
            match = " ".join(keywords) if keywords is not None else name
            if language == 'en':
                title = name
            if title is not None:
                url = title.replace(":", "").replace(" ", "-").replace(" ", "").lower()
            else:
                title = name
                url = None
            if language in ['hi', 'mr', 'te', 'bn', 'ta']:
                url = None
            elem = {
                'uid': name,
                'title': title,
                'subtitle': f'Copy "{emoji}" to clipboard',
                'arg': emoji,
                'match': match,
                'icon': {
                    'path': f'{icons_folder_path}/{name.replace(":", "")}.png',
                },
                'mods': {
                    'cmd': {
                        'subtitle': f'Paste "{emoji}" into frontmost application',
                    },
                    'alt': {
                        'subtitle': f'Copy ":{second_name}:" to clipboard',
                        'arg': f':{second_name}:'
                    },
                },
            }
            if url is not None:
                country = f'{language}' if language != 'en' else ''
                elem['mods'].update({
                    'shift': {
                        'subtitle': 'Find the emoji in emojipedia',
                        'arg': f'_web;{country}/{url}',
                        'icon': {
                            'path': 'icons/emojipedia.webp',
                        },
                    }
                })
            items.append(elem)
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
