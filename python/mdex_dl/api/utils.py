from typing import Any
import requests
from mdex_dl.models import ApiError


def require_ok_json(r: requests.Response) -> dict[str, Any]:
    """
    Checks health of API. Raise `ApiError` if things
    don't look good, else return `r.json()` to prevent
    parsing twice

    - `r` is the API response that has NOT already
    been converted to a dict [with r.json()]
    """
    try:
        r_json = r.json()
        result = r_json["result"]
    except ValueError:
        raise ApiError(
            f"Something has gone VERY wrong. ({r.status_code})"
            f"API response: {r.text}")

    if result != "ok":
        raise ApiError(
            f"API returned result {result}, "
            f"expected 'ok'. Status code {r.status_code}"
        )

    return r_json


def handle_ratelimit(): ...
