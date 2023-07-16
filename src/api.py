import os
import re
import sys
import json
import datetime
from urllib import request
sys.path.insert(0, './lib')
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
from utils import api_file_path, data_folder_path, icons_folder_path, display_notification, language

display_notification('⏳ Please wait !', 'Emojis data is beeing gathered, this can take some time...')

for folder in [data_folder_path, icons_folder_path]:
    if not os.path.exists(folder):
        os.mkdir(folder)

check_e_type = ['flag:', 'keycap:']

def convert_emoji_to_png(emoji, name):
    image_size = (128, 128)
    image = Image.new("RGBA", image_size, (0, 0, 0, 0))  # Set transparent background
    font_size = 64  # Adjusted font size
    font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    font = ImageFont.truetype(font_path, font_size, encoding='unic')
    draw_position = (int((image_size[0] - font_size) / 2), int((image_size[1] - font_size) / 2))
    draw = ImageDraw.Draw(image)
    draw.text(draw_position, emoji, font=font, embedded_color=True)
    image.save(f"{icons_folder_path}/{name.replace(':', '')}.png", "PNG")

try:
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
                if any(substring in name for substring in check_e_type):
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
        convert_emoji_to_png(emoji, name)

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