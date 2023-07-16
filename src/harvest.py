import os
import json
from utils import config, api_file_path, tags_file_path, icons_folder_path, language, data_folder_path

api_data = config(api_file_path)
tags_data = config(tags_file_path)
items = []

lib = os.getenv('_lib')
action = None
level = 0
if lib is not None:
    lib = lib.split(';')
    action, level, subaction, kID = lib[1], int(lib[2]), lib[3], lib[4]

if tags_data is None:
    try:
        os.mkdir(data_folder_path)
    except:
        pass
    with open(tags_file_path, 'w') as file:
        json.dump([], file)

with open('json/lang.json') as file:
    langs = json.load(file)
for item in langs:
    if item["value"] == language:
        lang = item["title"]
        break

if api_data:
    if level == 0:
        num_object = len(api_data['items'])
        items = [
            {
                'title': 'Refresh the API',
                'subtitle': f'Press ⏎ to grab emoji data with language : {lang}',
                'arg': '_api',
                'icon': {
                    'path': 'icons/sync.webp',
                },
            },
            {
                'title': 'Tags',
                'subtitle': f'Create, modify or remove tags for {lang}',
                'arg': '_rerun;;1;;',
                'icon': {
                    'path': 'icons/tag.webp',
                },
            },
            {
                'title': 'API information',
                'subtitle': f'Last update : {api_data["info"]["time"]} ǀ {num_object} Emojis ǀ {api_data["info"]["lang"]["title"]}',
                'valid': False,
                'icon': {
                    'path': 'icons/info.webp',
                },
            }
        ]
    else:
        for obj in tags_data:
            if obj['id'] == kID:
                title = obj['title']
                emojis_list = obj['emojis']
                break
        items.append({
            'title': 'Return',
            'subtitle': 'Back to previous state',
            'arg': f'_rerun;{action};{level - 1};;{kID}',
            'icon': {
                'path': 'icons/return.webp',
            },
        })
        if level == 1:
            for obj in [
                {
                    'title': 'Add a new tag',
                    'subtitle': 'Create a new tag and assign it to emojis',
                    'arg': f'_tags;new;;;{"ǀ".join(lib)}',
                    'icon': {
                        'path': 'icons/new.webp',
                    },
                },
                {
                    'title': 'Delete a tag',
                    'subtitle': 'Erase a tag from the list below',
                    'arg': '_rerun;delete;2;;',
                    'icon': {
                        'path': 'icons/delete.webp',
                    },
                }
            ]:
                items.append(obj)
            if tags_data is not None:
                for obj in tags_data:
                    list_emojis = ', '.join(obj['emojis'])
                    list_emojis = '❌ No Emojis' if list_emojis == '' else f'Emojis: {list_emojis}'
                    items.append({
                        'title': obj['title'] if obj['title'] != '' else 'No Title',
                        'subtitle': list_emojis,
                        'arg': f'_rerun;modify;2;;{obj["id"]}',
                        'icon': {
                            'path': 'icons/tag.webp',
                        },
                    })
        elif level == 2:
            if action == 'delete' and tags_data is not None:
                for obj in tags_data:
                    list_emojis = ', '.join(obj.get('emojis'))
                    list_emojis = '❌ No Emojis' if list_emojis == '' else f'Emojis: {list_emojis}'
                    items.append({
                        'title': obj['title'] if obj['title'] != '' else 'No Title',
                        'subtitle': list_emojis,
                        'arg': f'_tags;delete;;{obj["id"]};{"ǀ".join(lib)}',
                        'icon': {
                            'path': 'icons/tag.webp',
                        },
                    })
            elif action == 'modify' and tags_data is not None and api_data is not None:
                for obj in [
                    {
                        'title': 'Modify the Tag\'s name',
                        'subtitle': f"Current name: '{title}'",
                        'arg': f'_tags;modify;;{obj["id"]};{title};{"ǀ".join(lib)}',
                        'icon': {
                            'path': 'icons/tag.webp',
                        },
                    },
                    {
                        'title': 'Link an emoji',
                        'subtitle': 'Link the tag to emojis',
                        'arg': f'_rerun;modify;3;new;{kID}',
                        'icon': {
                            'path': 'icons/new.webp',
                        },
                    },
                    {
                        'title': 'Unlink an emoji',
                        'subtitle': 'Unlink the tag from emojis',
                        'arg': f'_rerun;modify;3;delete;{kID}',
                        'icon': {
                            'path': 'icons/delete.webp',
                        },
                    }
                ]:
                    items.append(obj)
                if emojis_list is not []:
                    filtered_data = [obj for obj in api_data['items'] if obj['emoji'] in emojis_list]
                    for obj in filtered_data:
                        items.append({
                            'title': obj['title'] if obj['title'] else obj['name'],
                            'valid': False,
                            'icon': {
                                'path': f'{icons_folder_path}/{obj["name"].replace(":", "")}.png',
                            },
                        })
        elif level == 3:
            if action == 'modify' and subaction == 'new':
                for obj in api_data['items']:
                    items.append({
                        'title': obj['title'] if obj['title'] else obj['name'],
                        'subtitle': f"Add '{title}' to '{obj['emoji']}'",
                        'arg': f'_tags;emoji;new;{kID};{obj["emoji"]};{"ǀ".join(lib)}',
                        'icon': {
                            'path': f'{icons_folder_path}/{obj["name"].replace(":", "")}.png',
                        },
                    })
            elif action == 'modify' and subaction == 'delete' and emojis_list is not []:
                filtered_data = [obj for obj in api_data['items'] if obj['emoji'] in emojis_list]
                for obj in filtered_data:
                    items.append({
                        'title': obj['title'] if obj['title'] else obj['name'],
                        'arg': f'_tags;emoji;delete;{kID};{obj["emoji"]};{"ǀ".join(lib)}',
                        'icon': {
                            'path': f'{icons_folder_path}/{obj["name"].replace(":", "")}.png',
                        },
                    })
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