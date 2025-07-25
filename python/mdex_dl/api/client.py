"""
Contains API utilities such as get_with_ratelimit(), which wraps the
Retry() session in mdex_dl.api.http_config to listen for MangaDex's
custom ratelimit headers (X-Ratelimit-*)
"""

import logging
from json import JSONDecodeError
import random
import time
from typing import Any

import requests

from mdex_dl.errors import ApiError
from mdex_dl.models import Chapter, Manga, Config, ReqsConfig


logger = logging.getLogger(__name__)


def safe_to_json(r: requests.Response) -> dict[str, Any] | None:
    """
    Checks if the provided response can be converted to JSON.

    An error is not raised to allow flexibility on caller side
    according to how critical parsing a response to JSON would be.

    Args:
        r (requests.Response): the response that's tested for JSON parsability

    Returns:
    -   dict: if the JSON response conversion is successful
    -   None: if unsuccessful
    """
    try:
        r_json = r.json()
    except JSONDecodeError:
        logger.warning("Failed to parse response as JSON for url: %s", r.url)
        logger.debug("API response as text: %s", r.text)

        return None

    if not isinstance(r_json, dict):
        logger.warning(
            "Unexpected JSON response type for url '%s': %s", r.url, type(r_json)
        )
        return None

    return r_json


def assert_ok_response(r_json: dict[str, Any]) -> None:
    """Checks that the JSON response (MangaDex) has a result key with value "ok" """
    if r_json.get("result") != "ok":
        logger.error("Non-ok response from API. Full JSON response: %s", r_json)
        raise ApiError("API returned non-ok response")


def get_cattributes(
    session: requests.Session, cfg: ReqsConfig, chapter: Chapter
) -> dict[str, Any]:
    """
    Sends a GET request to `api_root/chapter/chapter.id`

    Note: cattributes is short for **c**hapter **attributes**

    Reference:
        https://api.mangadex.org/docs/redoc.html#tag/Manga
    """
    r = session.get(f"{cfg.api_root}/chapter/{chapter.uuid}", timeout=cfg.get_timeout)

    if (r_json := safe_to_json(r)) is not None:
        assert_ok_response(r_json)
        return r_json["data"]["attributes"]
    raise ApiError("API returned a response that couldn't be parsed as JSON", r)


def get_with_ratelimit(
    url: str,
    session: requests.Session,
    cfg: Config,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    """
    Sends a GET request with the specified session and handles ratelimiting
    with the custom header `X-RateLimit-Retry-After`

    This essentially acts as a wrapper for `sessions.get(url, ...)`
    """

    if params is not None:
        r = session.get(url, timeout=cfg.reqs.get_timeout, params=params)
    else:
        r = session.get(url, timeout=cfg.reqs.get_timeout)

    if r.status_code != 429:
        return r
    logger.warning("Ratelimited (received status code 429)")

    try:
        retry_after = r.headers["X-RateLimit-Retry-After"]
    except KeyError:
        raise ApiError(
            "Ratelimit but not provided 'X-RateLimit-Retry-After' header", r
        ) from None

    logger.info("X-RateLimit-Retry-After = %s", retry_after)
    try:
        tts = int(int(retry_after) - time.time())
    except (ValueError, TypeError):
        raise ApiError(
            f"Expected type int from X-RateLimit-Retry-After, instead got {type(retry_after)}"
        ) from None

    logger.info("Time to sleep: %s seconds", tts)
    print(f"Ratelimited! Please wait {tts} seconds...")
    time.sleep(tts)
    time.sleep(random.uniform(0, cfg.retry.backoff_jitter))

    return session.get(url, timeout=cfg.reqs.get_timeout)


def get_manga_feed(
    session: requests.Session, cfg: Config, manga: Manga
) -> dict[str, Any]:
    """
    Sends a GET request to `/manga/manga.id/feed`

    Reference:
        https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-manga-id
    """

    feed = f"{cfg.reqs.api_root}/manga/{manga.uuid}/feed"

    if cfg.search.include_pornographic:
        r = session.get(
            feed,
            params={
                "translatedLanguage[]": ["en"],
                "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
            },
            timeout=cfg.reqs.get_timeout,
        )
    else:
        r = session.get(
            feed,
            timeout=cfg.reqs.get_timeout,
            params={"translatedLanguage[]": ["en"]},
        )

    logger.debug("get_manga_feed() raw text response from API: %s", r.text)

    if (r_json := safe_to_json(r)) is not None:
        assert_ok_response(r_json)
        return r_json
    raise ApiError("API returned a response that couldn't be parsed as JSON", r)
