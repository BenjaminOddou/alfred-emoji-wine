import os
import json

sound = os.environ['sound']
language = os.environ['language']
try:
    padding = int(os.environ['padding'])
except:
    padding = 10
cache_folder_path = os.environ['alfred_workflow_cache'] # ~/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.benjamino.emoji_wine
data_folder_path = os.environ['alfred_workflow_data'] # ~/Library/Application Support/Alfred/Workflow Data/com.benjamino.emoji_wine
api_file_path = f'{cache_folder_path}/api.json'
tags_file_path = f'{data_folder_path}/tags-{language}.json'
icons_folder_path = f'{cache_folder_path}/icons'

def display_notification(title: str, message: str):
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')
    os.system(f'"{os.getcwd()}/notificator" --message "{message}" --title "{title}" --sound "{sound}"')

def config(path: str):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return None
    with open(path, 'r') as file:
        return json.load(file)