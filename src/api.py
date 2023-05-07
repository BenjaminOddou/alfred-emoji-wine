import os
import re
import sys
sys.path.insert(0, './lib')
import base64
import json
import time
import datetime
from bs4 import BeautifulSoup
from io import BytesIO
from urllib import request
import xml.etree.ElementTree as ET
from utils import api_file_path, cache_folder_path, data_folder_path, icons_folder_path, display_notification, language

display_notification('⏳ Please wait !', 'Emojis data is beeing gathered, this can take some time...')
time.sleep(0.2)

for folder in [data_folder_path, cache_folder_path, icons_folder_path]:
    if not os.path.exists(folder):
        os.mkdir(folder)

try:
    img_urls = ['https://unicode.org/emoji/charts/full-emoji-list.html', 'https://unicode.org/emoji/charts/full-emoji-modifiers.html']
    for url in img_urls:
        img_response = request.urlopen(url).read().decode('utf-8')
        soup = BeautifulSoup(img_response, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows[1:]:
            cols = row.find_all('td')
            if cols:
                img_tag = cols[3].find('img')
                if img_tag:
                    img_src = img_tag.get('src').split(',')[1]
                    img_data = BytesIO(base64.b64decode(img_src))
                    file_name = f'{cols[-1].text.replace("⊛", "").replace(":", "").strip()}.png'
                    file_path = os.path.join(icons_folder_path, file_name)
                    with open(file_path, 'wb') as file:
                        file.write(img_data.getvalue())

    api_url = 'https://unicode.org/Public/emoji/latest/emoji-test.txt'
    api_response = request.urlopen(api_url).read().decode('utf-8')
    lines = [line.strip() for line in api_response.split('\n') if ('; fully-qualified' in line) or ('; component' in line)]
    
    lang_url_1 = f'https://raw.githubusercontent.com/unicode-org/cldr/main/common/annotations/{language}.xml'
    lang_url_2 = f'https://raw.githubusercontent.com/unicode-org/cldr/main/common/annotationsDerived/{language}.xml'
    lang_response_1 = request.urlopen(lang_url_1).read().decode('utf-8')
    lang_response_2 = request.urlopen(lang_url_2).read().decode('utf-8')

    root = ET.fromstring(lang_response_1)
    root.extend(ET.fromstring(lang_response_2))

    items = []
    for line in lines:
        array = re.split(r'\bfully-qualified\b|\bcomponent\b', line)[1].strip().split(' ', 3)
        emoji, name = array[1], array[-1]
        trim_emoji = re.sub('\uFE0F', '', emoji)
        for elem in root:
            tags_list = elem.find(f"./annotation[@cp='{trim_emoji}']")
            title = elem.find(f"./annotation[@cp='{trim_emoji}'][@type='tts']")
            tags = None
            if tags_list is not None and title is not None:
                title = title.text
                if 'flag:' in name:
                    tags = title.replace(':', '').split(' ')
                    for i in range(len(tags)):
                        tags[i] = tags[i].strip()
                else:
                    tags = tags_list.text.split(' | ')
                break
        items.append({
            'name': name,
            'emoji': emoji,
            'title': title,
            'tags': tags
        })

    with open('json/lang.json') as file:
        langs = json.load(file)
    for item in langs:
        if item["value"] == language:
            lang = item["title"]
            break
    info = {'time': datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), 'lang': {'title': lang, 'value': language}}
    with open(api_file_path, 'w', encoding='utf-8') as file:
        json.dump({'info': info, 'items': items}, file, ensure_ascii=False, indent=4)

    display_notification('✅ Success !', 'Data updated. You can search emojis')
except:
    display_notification('🚨 Error !', 'Something went wrong, check your internet connexion or create a GitHub issue')