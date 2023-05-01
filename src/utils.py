import os
import json

sound = os.environ['sound']
language = os.environ['language']
cache_folder_path = os.environ['alfred_workflow_cache'] #  ~/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.benjamino.emoji_wine
api_file_path = f'{cache_folder_path}/api.json'
icons_folder_path = f'{cache_folder_path}/icons'

def display_notification(title: str, message: str):
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')
    os.system(f'"{os.getcwd()}/notificator" --message "{message}" --title "{title}" --sound "{sound}"')

def api():
    if not os.path.isfile(api_file_path) or os.path.getsize(api_file_path) == 0:
        return None
    with open(api_file_path, 'r') as file:
        return json.load(file)