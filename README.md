<img src="public/icon_dark_mode.webp#gh-dark-mode-only" alt="logo-dark" height="55"/>
<img src="public/icon_light_mode.webp#gh-light-mode-only" alt="logo-light" height="55"/>

[![made with heart by Benjamin Oddou](https://img.shields.io/badge/made%20with%20%E2%99%A5%20by-benjamin%20oddou-ff2f35.svg?style=flat)](https://github.com/BenjaminOddou)
[![saythanks](https://img.shields.io/badge/say-thanks-bf0001.svg?style=flat)](https://saythanks.io/to/BenjaminOddou)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-7f0000.svg)](https://www.python.org/downloads/macos/)

Welcome to the Alfred Emoji Wine repository: **An Alfred Workflow** ✨

## ✅ Prerequisites

* MacOS.
* Alfred 5. Note that the [Alfred Powerpack](https://www.alfredapp.com/powerpack/) is required to use workflows.
* Requires **python 3.8** or above.
* Requires [pillow](https://formulae.brew.sh/formula/pillow) library.

## 🏎️ Data sources

This workflow combines multiple sources (see below) to build a local JSON API (`~/Library/Caches/com.runningwithcrayons.Alfred/Workflow Data/com.benjamino.emoji_wine`) along with an icons folder with png images.

List of sources :
* [Full list of latest emojis](https://unicode.org/Public/emoji/latest/emoji-test.txt) - Used to grab the full list of emojis.
* [CLDR Data files annotations](https://github.com/unicode-org/cldr/tree/main/common/annotations) - Used to translate emojis titles and tags.
* [CLDR Data files annotations derived](https://github.com/unicode-org/cldr/tree/main/common/annotationsDerived) - Used to translate emojis titles and tags.

## ⬇️ Installation

1. [Download the workflow](https://github.com/BenjaminOddou/alfred-emoji-wine/releases/latest)
2. Double click the `.alfredworkflow` file to install

## 🧰 Setup the workflow

Install Python 3.8 or above. Check your version with :

```shell
python --version
```

Install [pillow](https://formulae.brew.sh/formula/pillow) using Homebrew :

```shell
brew install pillow
```

## 🧙‍♂️ Invoke the workflow

There is 2 flows in this workflow :

1. The first one allows you to display emojis. It can be triggered by writing `wine` keyword.
2. The second allows you to build the local api according the selected language. You can invoke this flow with the `harvest` keyword.

You can edit these triggers (flagged with a `🕹️` symbol) in the user configuration panel.

## 🤖 Usage of the workflow

### Setup variables

1. `🌐 Language` : select the language you prefer. Here is the full list of supported languages :

| **Language**       | **ISO639-1** | **EmojiPedia** | **EmojiTerra** | **EmojiAll** |
|--------------------|--------------|----------------|----------------|--------------|
| 🇬🇧 English       | en           | 🟢             | 🟢             | 🟢           |
| 🇫🇷 Français      | fr           | 🟢             | 🟢             | 🟢           |
| 🇪🇸 Español       | es           | 🟢             | 🟢             | 🟢           |
| 🇵🇹 Português     | pt           | 🟢             | 🟢             | 🟢           |
| 🇮🇹 Italiano      | it           | 🟢             | 🟢             | 🟢           |
| 🇩🇪 Deutsch       | de           | 🟢             | 🟢             | 🟢           |
| 🇳🇱 Nederlands    | nl           | 🟢             | 🔴             | 🟢           |
| 🇳🇴 Norsk         | no           | 🟢             | 🔴             | 🔴           |
| 🇸🇪 Svenska       | sv           | 🟢             | 🔴             | 🟢           |
| 🇩🇰 Dansk         | da           | 🟢             | 🔴             | 🟢           |
| 🇮🇩 Melayu        | ms           | 🟢             | 🔴             | 🟢           |
| 🇸🇦 ٱلْعَرَبِيَّة | ar           | 🔴             | 🔴             | 🟢           |
| 🇷🇺 Русский       | ru           | 🔴             | 🔴             | 🟢           |
| 🇨🇳 中文            | zh           | 🟢             | 🔴             | 🔴           |
| 🇨🇳 繁體中文          | zh-hant      | 🔴             | 🔴             | 🟢           |
| 🇯🇵 日本語           | ja           | 🟢             | 🔴             | 🟢           |
| 🇰🇷 한국어           | ko           | 🟢             | 🔴             | 🟢           |
| 🇮🇳 हिंदी         | hi           | 🔴             | 🔴             | 🟢           |
| 🇮🇳 मराठी         | mr           | 🔴             | 🔴             | 🔴           |
| 🇮🇳 తెలుగు        | te           | 🔴             | 🔴             | 🔴           |
| 🇧🇩 বাংলা         | bn           | 🔴             | 🔴             | 🔴           |
| 🇱🇰 தமிழ்         | ta           | 🔴             | 🔴             | 🔴           |


> All emojis aren't translated in all languages. Some languages aren't supported by emoji dictionnaries.

If you wish to use another language, open a GitHub issue [here](https://github.com/BenjaminOddou/alfred-emoji-wine/issues/new).

2. `✂️ Padding` : Add transparent margins to icons (in pixels).

3. `🪩 Style` : Select between list or grid view.

4. `📖 Emoji Dictionary` : Select your online emoji dictionary.

5. `🌈 Skin Tone` : Select your preferred skin tone.

6. `🎷 Notification sound` : Personalize the sound of the workflow notification.

### Search an emoji

Trigger the workflow with `wine` keyword and search for an your emoji in the selected language.

![search](public/search.webp)

### Workflow actions

1. Press <kbd>⏎</kbd> on the selected emoji to copy it to the clipboard.
2. Press <kbd>⌘</kbd><kbd>⏎</kbd> on the selected emoji to paste it to the frontmost application.
3. Press <kbd>⇧</kbd><kbd>⏎</kbd> on the selected emoji to open its emojipedia page in the selected language.

### Refresh the API and configure tags

> Use the `harvest` keyword.

In the following menu you'll find :
1. A button to refresh the API for the selected language.
2. The Tags section for the selected language.
3. The last API information with date and time of the last update, number of emojis and the language selected when the API was created.

![harvest](public/harvest.webp)

Tags can be created and linked to one or multiple emojis.

![tag](public/tag.webp)

This allows to search emojis using custom words or phrases.

![search_tag](public/search_tag.webp)

> Tags are language specific meaning that when created they will impact only the selected language. They are also persistent overtime meaning that if you switch language or refresh the API, they will not be erased. Tags are stored under JSON files located in the `afred_workflow_data` folder (`~/Library/Application Support/Alfred/Workflow Data/com.benjamino.emoji_wine`).

## ⚖️ License

[MIT License](LICENSE) © Benjamin Oddou
