import json
from utils import config, api_file_path, tags_file_path, icons_folder_path, language

api_data = config(api_file_path)
tags_data = config(tags_file_path)
items = []

with open('json/lang.json') as file:
    langs = json.load(file)
for item in langs:
    if item["value"] == language:
        lang = item["title"]
        break

if api_data:
    if language != api_data['info']['lang']['value']:
        items.append({
            'title': 'Refresh the API',
            'subtitle': f'Press ⏎ to grab emoji data with language : {lang}',
            'arg': '_api',
            'icon': {
                'path': 'icons/info.webp',
            },
        })
    else:
        for item in api_data['items']:
            name, emoji, title, tags = item['name'], item['emoji'], item['title'], item['tags']
            second_name = name.replace(" ", "_").replace(":", "").lower()
            match = " ".join(tags) if tags is not None else name
            if tags_data is not None:
                for tag in tags_data:
                    for tag_emoji in tag['emojis']:
                        if tag_emoji == emoji:
                            match += f' {tag["title"]}'
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
        'subtitle': f'Press ⏎ to grab emoji data with language : {lang}',
        'arg': '_api',
        'icon': {
            'path': 'icons/info.webp',
        },
    })

print(json.dumps({'items': items}))
