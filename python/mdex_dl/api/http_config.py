"""
Contains the retry config used for requests sessions.
"""

import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from mdex_dl.load_config import RetryConfig


logger = logging.getLogger(__name__)


def get_retry_adapter(cfg: RetryConfig):
    """Creates a Retry() config with the given config cfg"""
    retry_config = Retry(
        total=cfg.max_retries,
        backoff_factor=cfg.backoff_factor,
        backoff_jitter=cfg.backoff_jitter,
        backoff_max=cfg.backoff_max,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods={"GET"},
        respect_retry_after_header=False,  # MangaDex sends non-conventional "X-*" headers
    )
    logger.debug("Created HTTPAdapter()")
    return HTTPAdapter(max_retries=retry_config)
