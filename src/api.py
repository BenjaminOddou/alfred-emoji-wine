import os
import sys
import shutil
import subprocess
from utils import (
    api_file_path,
    data_folder_path,
    icons_folder_path,
    assets_folder_path,
    display_notification,
    language,
    padding,
    custom_logger,
    langs,
    workflow_version,
)


def get_homebrew_prefix():
    try:
        prefix = subprocess.check_output(["brew", "--prefix"])
        return prefix
    except:
        return None


homebrew_prefix = get_homebrew_prefix()

if homebrew_prefix:
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    pillow_dir = f"{homebrew_prefix}/Cellar/pillow"
    try:
        latest_version = max(os.listdir(pillow_dir))
        pillow_path = os.path.join(
            pillow_dir, latest_version, f"lib/python{python_version}/site-packages"
        )
        sys.path.append(pillow_path)
    except:
        pass

import re
import json
import datetime
from urllib import request
import xml.etree.ElementTree as ET

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception as e:
    display_notification(
        "🚨 Error !", "Pillow is not detected, check the documentation to install it"
    )
    custom_logger("error", e)
    exit()

display_notification(
    "⏳ Please wait !", "Emojis data is beeing gathered, this can take some time..."
)

if os.path.exists(icons_folder_path):
    shutil.rmtree(icons_folder_path)

os.mkdir(icons_folder_path)

if not os.path.exists(data_folder_path):
    os.mkdir(data_folder_path)

check_e_type = ["flag:", "keycap:"]


def is_blank_image(image):
    """Efficiently checks if an image is blank (fully transparent or one solid color)."""
    pixels = image.getdata()
    first_pixel = next(
        iter(pixels)
    )  # Get the first pixel without loading all into memory

    all_same = True
    all_transparent = True

    for pixel in pixels:
        if pixel != first_pixel:
            all_same = False
        if pixel[3] != 0:  # Check transparency (alpha channel)
            all_transparent = False
        if not all_same and not all_transparent:
            return False  # Exit early if image is neither blank nor fully transparent

    return all_same or all_transparent  # Returns True if either condition is met


def convert_emoji_to_png(emoji, name):
    image_size = (64 + padding, 64 + padding)  # set image size
    image = Image.new("RGBA", image_size, (0, 0, 0, 0))  # Set transparent background
    font_size = 64  # Adjusted font size
    font_path = "/System/Library/Fonts/Apple Color Emoji.ttc"
    font = ImageFont.truetype(font_path, font_size, encoding="unic")
    draw_position = (
        int((image_size[0] - font_size) / 2),
        int((image_size[1] - font_size) / 2),
    )
    draw = ImageDraw.Draw(image)
    draw.text(draw_position, emoji, font=font, embedded_color=True)
    if is_blank_image(image):
        raise ValueError(f"Generated image for '{emoji}' is blank or unsupported.")
    image.save(f"{icons_folder_path}/{name.replace(':', '')}.png", "PNG")


def remove_skin_tones(emoji):
    skin_tone_range = range(0x1F3FB, 0x1F3FF + 1)
    clean_emoji = "".join([char for char in emoji if ord(char) not in skin_tone_range])
    return clean_emoji


def get_skin_tones(emoji):
    skin_tones = []
    if emoji in cleaned_emojis:
        skin_tones.append("none")
    else:
        skin_tone_dict = {
            0x1F3FB: "light skin tone",
            0x1F3FC: "medium-light skin tone",
            0x1F3FD: "medium skin tone",
            0x1F3FE: "medium-dark skin tone",
            0x1F3FF: "dark skin tone",
        }
        for char in emoji:
            value_skin_tone = skin_tone_dict.get(ord(char))
            if value_skin_tone:
                skin_tones.append(value_skin_tone)
        if not skin_tones:
            skin_tones.append("base")
    return list(set(skin_tones))


skin_tones = [
    "light skin tone",
    "medium-light skin tone",
    "medium skin tone",
    "medium-dark skin tone",
    "dark skin tone",
]

try:
    api_url = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
    api_response = request.urlopen(api_url).read().decode("utf-8")
    lines = [
        line.strip()
        for line in api_response.split("\n")
        if ("; fully-qualified" in line) or ("; component" in line)
    ]

    lang_url_1 = f'https://raw.githubusercontent.com/unicode-org/cldr/main/common/annotations/{language.replace("-", "_")}.xml'
    lang_url_2 = f'https://raw.githubusercontent.com/unicode-org/cldr/main/common/annotationsDerived/{language.replace("-", "_")}.xml'
    lang_response_1 = request.urlopen(lang_url_1).read().decode("utf-8")
    lang_response_2 = request.urlopen(lang_url_2).read().decode("utf-8")

    root = ET.fromstring(lang_response_1)
    root.extend(ET.fromstring(lang_response_2))

    items = []
    cleaned_emojis = []
    full_emojis = []

    for line in lines:
        array = (
            re.split(r"\bfully-qualified\b|\bcomponent\b", line)[1]
            .strip()
            .split(" ", 3)
        )
        emoji, name = array[1], array[-1]
        full_emojis.append({"emoji": emoji, "name": name})
        clean_emoji = remove_skin_tones(emoji)
        if emoji != clean_emoji:
            cleaned_emojis.append(clean_emoji)

    for obj in full_emojis:
        emoji, name = obj["emoji"], obj["name"]
        trim_emoji = re.sub("\ufe0f", "", emoji)
        for elem in root:
            tags_list = elem.find(f"./annotation[@cp='{trim_emoji}']")
            title = elem.find(f"./annotation[@cp='{trim_emoji}'][@type='tts']")
            tags = None
            if tags_list is not None and title is not None:
                title = title.text
                if any(substring in name for substring in check_e_type):
                    tags = title.replace(":", "").split(" ")
                    for i in range(len(tags)):
                        tags[i] = tags[i].strip()
                else:
                    tags = tags_list.text.split(" | ")
                tags.append(emoji)
                break
        try:
            convert_emoji_to_png(emoji, name)
            image = True
        except Exception as e:
            custom_logger("error", f"{emoji} cannot be transform into an image, {e}")
            image = False
        items.append(
            {
                "name": name,
                "emoji": emoji,
                "title": title,
                "tags": tags,
                "image": image,
                "skin_tones": get_skin_tones(emoji),
            }
        )

    for item in langs:
        if item["value"] == language:
            lang = item["title"]
            break
    info = {
        "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "lang": {"title": lang, "value": language},
        "workflow_version": workflow_version,
    }
    with open(api_file_path, "w", encoding="utf-8") as file:
        json.dump({"info": info, "items": items}, file, ensure_ascii=False, indent=4)

    assets = [f for f in os.listdir(assets_folder_path)]

    for i in assets:
        image_path = os.path.join(assets_folder_path, i)
        image = Image.open(image_path)
        width, height = image.size
        new_image = Image.new("RGBA", (width + padding, height + padding), (0, 0, 0, 0))
        new_image.paste(image, (int(padding / 2), int(padding / 2)))
        output_path = os.path.join(icons_folder_path, i)
        new_image.save(output_path)

    display_notification("✅ Success !", "Data updated. You can search emojis")
    custom_logger("info", f"API refreshed with language : {language}")
except Exception as e:
    display_notification(
        "🚨 Error !", "Something went wrong, check the logs and create a GitHub issue"
    )
    custom_logger("error", e)
