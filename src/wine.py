#!/usr/bin/env python3

import re
import json
from utils import config, api_file_path, tags_file_path, icons_folder_path, language, emoji_dictionary, langs, workflow_version, skin_tone

api_data = config(api_file_path)
tags_data = config(tags_file_path)
items = []

for item in langs:
    if item["value"] == language:
        lang = item["title"]
        break

if api_data:
    if language != api_data['info']['lang']['value'] or workflow_version != api_data['info'].get('workflow_version'):
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
            name, emoji, title, tags, image, skin_tones = item['name'], item['emoji'], item['title'], item['tags'], item['image'], item['skin_tones']
            match = " ".join([title] + tags) if tags is not None else name
            if tags_data is not None:
                for tag in tags_data:
                    for tag_emoji in tag['emojis']:
                        if tag_emoji == emoji:
                            match += f' {tag["title"]}'
            if language == 'en':
                title = name
            if emoji_dictionary == 'emojiall.com':
                url = f'emoji/{emoji}'
            elif title is not None:
                url = re.sub(r'[:(), ]', '', title)
                url = re.sub(r'[’ ]', '-', url).lower()
            else:
                title = name
                url = None
            icon_path = f'{icons_folder_path}/{name.replace(":", "")}.png' if image else f'{icons_folder_path}/unicode.png'
            elem = {
                'uid': name,
                'title': title,
                'subtitle': f'Copy "{emoji}" to clipboard',
                'arg': emoji,
                'match': match,
                'icon': {
                    'path': icon_path,
                },
                'mods': {
                    'cmd': {
                        'subtitle': f'Paste "{emoji}" into frontmost application',
                    },
                },
            }
            if url is not None:
                country = f'{language.lower()}/' if language != 'en' else ''
                elem['mods'].update({
                    'shift': {
                        'subtitle': f'Find the emoji in {emoji_dictionary}',
                        'arg': f'_web;https://{emoji_dictionary}/{country}{url}',
                        'icon': {
                            'path': f'{icons_folder_path}/{emoji_dictionary.split(".")[0]}.png',
                        },
                    }
                })
            if skin_tone in skin_tones or 'base' in skin_tones or skin_tone == 'all':
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
