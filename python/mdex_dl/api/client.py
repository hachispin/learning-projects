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
from mdex_dl.models import Chapter, Config


logger = logging.getLogger(__name__)


def safe_get_json(
    url: str,
    session: requests.Session,
    cfg: Config,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Retrieves the JSON response using the given session by sending a GET
    request to the provided URL.

    Args:
        url (str): where to send the GET request to
        session (requests.Session): the client used that should have a retry adapter
        cfg (Config): used for args like timeout
        params (dict[str, Any] | None, optional): args passed to the URL. Defaults to None.

    Raises:
        ApiError: if the response is not JSON parsable or anything else goes wrong

    Returns:
        dict ([str, Any]): the JSON response
    """

    # just a design choice, but i raise if it's not json parsable
    # instead of retrying. i do this because errors like these
    # are usually the client's fault.  /_ \

    logger.debug("Retrieving JSON from url: %s", url)
    r = get_with_ratelimit(url, session, cfg, params)
    logger.debug("Raw response received: %s", r.text)

    try:
        r_json = r.json()
    except JSONDecodeError:
        logger.warning("Failed to decode response into JSON")
        raise ApiError("Request failed (JSONDecodeError)", r) from None

    assert_ok_response(r_json)

    if not isinstance(r_json, dict):
        logger.warning(
            "Expected type dict for JSON response, instead got %s", type(r_json)
        )
        raise ApiError("Malformed response (incorrect type)", r)

    return r_json


def assert_ok_response(r_json: dict[str, Any]) -> None:
    """Checks that the JSON response (MangaDex) has a result key with value "ok" """
    if r_json.get("result") != "ok":
        logger.error("Non-ok response from API. Full JSON response: %s", r_json)
        raise ApiError("API returned non-ok response")


def get_cattributes(
    session: requests.Session, cfg: Config, chapter: Chapter
) -> dict[str, Any]:
    """
    Sends a GET request to `api_root/chapter/chapter.id`

    Note: cattributes is short for **c**hapter **attributes**

    Reference:
        https://api.mangadex.org/docs/redoc.html#tag/Mangas
    """
    endpoint = f"{cfg.reqs.api_root}/chapter/{chapter.uuid}"
    return safe_get_json(endpoint, session, cfg)


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

    # imitating Retry() behaviour
    logger.info("Time to sleep: %s seconds", tts)
    print(f"Ratelimited! Please wait {tts} seconds...")
    time.sleep(tts)
    time.sleep(random.uniform(0, cfg.retry.backoff_jitter))

    return session.get(url, timeout=cfg.reqs.get_timeout)
