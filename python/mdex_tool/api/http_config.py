"""
Contains the retry config used for requests sessions.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mdex_tool.load_config import RetryConfig


def _get_retry_adapter(retry_cfg: RetryConfig):
    """Creates a Retry() config with the given config cfg"""
    retry_config = Retry(
        total=retry_cfg.max_retries,
        backoff_factor=retry_cfg.backoff_factor,
        backoff_jitter=retry_cfg.backoff_jitter,
        backoff_max=retry_cfg.backoff_max,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET"},
        respect_retry_after_header=False,  # MangaDex sends non-conventional "X-*" headers
    )
    return HTTPAdapter(max_retries=retry_config)

def get_retry_session(retry_cfg: RetryConfig) -> requests.Session:
    """Returns a session mounted with the retry adapter from `get_retry_adapter()`"""
    session = requests.session()
    adapter = _get_retry_adapter(retry_cfg)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session
