import os
import json
import logging as log
import xml.etree.ElementTree as ET

def langs_dict(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    languages = []
    array = root.find(".//dict[string='🌐 Language']/dict/array")
    for node in array:
        title = node.find("string[1]").text
        value = node.find("string[2]").text
        languages.append({"title": title, "value": value})
    return languages

# Langs dict
langs = langs_dict('info.plist')

sound = os.environ['sound']
language = os.environ['language']
try:
    padding = int(os.environ['padding'])
except:
    padding = 10
cache_folder_path = os.environ['alfred_workflow_cache'] # ~/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.benjamino.emoji_wine
data_folder_path = os.environ['alfred_workflow_data'] # ~/Library/Application Support/Alfred/Workflow Data/com.benjamino.emoji_wine
workflow_version = os.environ['alfred_workflow_version']
for folder in [cache_folder_path, data_folder_path]:
    os.makedirs(folder, exist_ok=True)
assets_folder_path = f'{os.getcwd()}/icons/assets'
api_file_path = f'{cache_folder_path}/api.json'
tags_file_path = f'{data_folder_path}/tags-{language}.json'
icons_folder_path = f'{cache_folder_path}/icons'
emoji_dictionary = os.environ['emoji_dictionary'] # https://emojipedia.org

def display_notification(title: str, message: str):
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')
    os.system(f'"{os.getcwd()}/notificator" --message "{message}" --title "{title}" --sound "{sound}"')

def config(path: str):
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return None
    with open(path, 'r') as file:
        return json.load(file)

# Init logger
logger = log.getLogger('plex')
logger.setLevel(log.DEBUG)
log_file_handler = log.FileHandler(os.path.join(cache_folder_path, f'emoji_wine.log'))
log_file_handler.setLevel(log.DEBUG)
log_formatter = log.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file_handler.setFormatter(log_formatter)
logger.addHandler(log_file_handler)

def custom_logger(level: str, message: str):
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)