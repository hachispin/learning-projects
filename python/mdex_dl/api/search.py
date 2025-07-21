"""WIP"""

import logging

from mdex_dl.load_config import SearchConfig
from mdex_dl.api.http_config import get_retry_adapter

logger = logging.getLogger(__name__)


class Searcher:
    """
    NOTE: There should only be one instance of this class
    used throughout the program's class
    """

    def __init__(self, cfg: SearchConfig):
        self.cfg = cfg
