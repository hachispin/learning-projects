"""
Contains common functions such as `safe_get_req()`, which
is used to retry GET requests while complying with ratelimits
and raising `ApiError` if needed
"""

from mdex_dl.models import Chapter, Manga, ApiError

# for jitter
import time
import random

from pathlib import Path
from typing import Any
import requests
import logging


def sleep_with_jitter(base_delay: float):
    time.sleep(random.uniform(base_delay, base_delay * 2))


def safe_get_req(url: str, max_retries: int) -> requests.Response:
    """
    Sends a GET request to `url` and returns its response with proper
    ratelimit handling based on:

    -   the configured `max_retries`
    -   the header, `X-RateLimit-Retry-After`

    If `max_retries` is exceeded, raises `APIError`

    Reference:
        https://api.mangadex.org/docs/2-limitations/#endpoint-specific-rate-limits
    """
    for i in range(max_retries + 1):
        r = requests.get(url)

        if r.status_code == 429:  # Ratelimited!
            logging.warning("Ratelimited")
            # Retry-After is a UNIX timestamp
            retry_after = int(r.headers.get("X-RateLimit-Retry-After", -1))

            if retry_after == -1:
                logging.warning("Retry-After not provided after being ratelimited")
                tts = 1

            tts = retry_after - time.time()
            logging.info("Retrying in: %s seconds (+ jitter)", round(tts, 2))
            sleep_with_jitter(tts)

    raise ApiError("...")


def get_cattributes(api_root, chapter: Chapter) -> dict[str, Any]:
    """
    Sends a GET request to `api_root`/chapter/`chapter.id`

    Note: cattributes is short for **c**hapter **attributes**

    Reference:
        https://api.mangadex.org/docs/redoc.html#tag/Manga
    """
    r = requests.get(f"{api_root}/chapter/{chapter.id}")
    r_json = require_ok_json(r)

    return r_json["data"]["attributes"]


def get_mattributes(api_root, manga: Manga) -> dict[str, Any]:
    """
    Sends a GET request to `api_root`/manga/`manga.id`

    Note: mattributes is short for **m**anga **attributes**

    Reference:
        https://api.mangadex.org/docs/redoc.html#tag/Chapter/operation/get-chapter-id
    """
    r = requests.get(f"{api_root}/manga/{manga.id}")
    r_json = require_ok_json(r)

    return r_json["data"]["attributes"]


def handle_ratelimit(): ...


# this doesn't really fit but it's whatever
def get_project_root() -> Path:
    return Path(__file__).resolve().parent
