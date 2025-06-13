import os
import json
import sys
import secrets
from utils import (
    config,
    api_file_path,
    tags_file_path,
    display_notification,
    custom_logger,
)

action = os.environ["split2"]
subaction = os.environ["split3"]
tagID = os.environ["split4"]
api = config(api_file_path)
tags = config(tags_file_path)
data = []
if tags is not None:
    for obj in tags:
        data.append(obj)
if action == "new":
    print(os.environ["split5"], end="")
    data.append(
        {"id": secrets.token_hex(6), "title": sys.argv[1].strip(), "emojis": []}
    )
elif action == "delete":
    print(os.environ["split5"], end="")
    for obj in data:
        if obj["id"] == tagID:
            data.remove(obj)
            break
elif action == "modify":
    print(os.environ["split6"], end="")
    for obj in data:
        if obj["id"] == tagID:
            obj["title"] = sys.argv[1].strip()
            break
elif action == "emoji":
    print(os.environ["split6"], end="")
    if subaction == "new":
        for obj in data:
            if obj["id"] == tagID:
                obj["emojis"].append(os.environ["split5"])
                obj["emojis"] = list(set(obj["emojis"]))
                break
    elif subaction == "delete":
        for obj in data:
            if obj["id"] == tagID:
                obj["emojis"].remove(os.environ["split5"])
                break
else:
    display_notification(
        "🚨 Error !",
        "Something went wrong, check the logs and report it as a GitHub issue",
    )
    custom_logger(
        "error",
        'The action os.environ["split2"] is not in the following list {new, delete, modify, emoji}',
    )
    exit()

with open(tags_file_path, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)
