"""Remote data sources (Unicode + CLDR)."""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Tuple
from urllib import request

USER_AGENT = "alfred-emoji-wine (+https://github.com/BenjaminOddou/alfred-emoji-wine)"
TIMEOUT = 30
EMOJI_TEST_URL = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
CLDR_URL = "https://raw.githubusercontent.com/unicode-org/cldr/main/common/{folder}/{language}.xml"

Fetcher = Callable[[str], str]


def fetch_url(url: str) -> str:
    req = request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with request.urlopen(req, timeout=TIMEOUT) as response:
            return response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to fetch %s : %s" % (url, exc)) from exc


def cldr_urls(language: str) -> Tuple[str, str]:
    code = language.replace("-", "_")
    return (
        CLDR_URL.format(folder="annotations", language=code),
        CLDR_URL.format(folder="annotationsDerived", language=code),
    )


def fetch_all(language: str, fetch: Fetcher = fetch_url) -> Tuple[str, str, str]:
    """Download emoji-test, annotations and derived annotations concurrently."""
    urls = (EMOJI_TEST_URL,) + cldr_urls(language)
    with ThreadPoolExecutor(max_workers=len(urls)) as pool:
        emoji_test, annotations, derived = pool.map(fetch, urls)
    return emoji_test, annotations, derived
