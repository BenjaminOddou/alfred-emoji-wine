#!/usr/bin/env python3

import re
import json
from utils import config, api_file_path, tags_file_path, icons_folder_path, language, emoji_dictionary, langs, workflow_version, skin_tone, short_copy, short_paste, short_web

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
                'match': match,
                'icon': {
                    'path': icon_path,
                },
            }
            mod = {}
            if short_copy == 'arg':
                elem['subtitle'] = f'Copy "{emoji}" to the clipboard'
                elem['arg'] = f'_copy;{emoji}'
            elif short_copy:
                mod.update({
                    short_copy: {
                        'subtitle': f'Press ⏎ to copy "{emoji}" to the clipboard',
                        'arg': f'_copy;{emoji}',
                    }
                })
            if short_paste == 'arg':
                elem['subtitle'] = f'Paste "{emoji}" into frontmost application'
                elem['arg'] = f'_paste;{emoji}'
            elif short_paste:
                mod.update({
                    short_paste: {
                        'subtitle': f'Press ⏎ to paste "{emoji}" into frontmost application',
                        'arg': f'_paste;{emoji}',
                    }
                })
            if url is not None:
                country = f'{language.lower()}/' if language != 'en' else ''
                if short_web == 'arg':
                    elem['subtitle'] = f'Find the emoji in {emoji_dictionary}'
                    elem['arg'] = f'_web;https://{emoji_dictionary}/{country}{url}'
                elif short_web:
                    mod.update({
                        short_web: {
                            'subtitle': f'Press ⏎ to find the emoji in {emoji_dictionary}',
                            'arg': f'_web;https://{emoji_dictionary}/{country}{url}',
                            'icon': {
                                'path': f'{icons_folder_path}/{emoji_dictionary.split(".")[0]}.png',
                            },
                        }
                    })
            if mod:
                elem['mods'] = mod
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

print(json.dumps({'items': items}, ensure_ascii=False))
