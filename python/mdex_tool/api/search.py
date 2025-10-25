"""Contains the Searcher() class."""

import logging
from typing import Any

from mdex_tool.models import Config, Manga, MangaResults
from mdex_tool.api.http_config import get_retry_session
from mdex_tool.api.client import safe_get_json

logger = logging.getLogger(__name__)


class Searcher:
    """
    Contains searching functionality.

    NOTE: There should only be one instance of this class
    created throughout the program's runtime.
    """

    def __init__(self, cfg: Config):
        self.session = get_retry_session(cfg.retry)
        self.cfg = cfg

    def _safe_get_json(self, url: str, params: dict[str, Any] | None = None):
        """Packages safe_get_json() from .api.client into a method."""
        return safe_get_json(url, self.session, self.cfg, params)

    def _get_title(self, mattributes: dict) -> str:
        """
        Tries to get a manga's title by trying multiple language codes.

        Args:
            mattributes (dict): the ["attributes"] key of a manga from `GET /manga` or search result

        Returns:
            str: the title
        """
        titles = mattributes.get("title", {})

        return titles.get("en") or titles.get("ja-ro") or titles.get("ja") or "Untitled"

    def search(self, query: str, page: int = 0) -> MangaResults:
        """
        Searches for the given query and returns a list of Manga UUIDs.

        By default, this sorts by descending relevance to the query, along
        with other search parameters for better UX when downloading.

        Pornographic results will only be included if configured as such.

        Args:
            query (str): the search query, which should match a manga's title
            page (int, optional): which page to query.

                The number of chapters returned is
                dependent on `cfg.search.results_per_page` (config).

        Returns:
            MangaResults: the results for the selected page as
                `tuple[Manga, ...]` and the total number of results
        """
        params = {
            "title": query,
            "order[relevance]": "desc",
            "hasAvailableChapters": "true",  # not perfect; chapters w/ 0 pages exist
            "availableTranslatedLanguage[]": ["en"],
            "limit": self.cfg.search.results_per_page,
            "offset": self.cfg.search.results_per_page * page,
        }  # Ref: https://api.mangadex.org/docs/redoc.html#tag/Manga/operation/get-search-manga

        if self.cfg.search.include_pornographic:
            params = {
                **params,
                "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
            }
        logger.info(
            "Searching for query '%s' on page %s. Pornographic results included: %s",
            query,
            page,
            self.cfg.search.include_pornographic,
        )

        endpoint = f"{self.cfg.reqs.api_root}/manga"
        r_json = self._safe_get_json(endpoint, params)
        results: list[Manga] = []

        for m in r_json["data"]:
            results.append(Manga(self._get_title(m["attributes"]), m["id"]))

        return MangaResults(tuple(results), total=r_json["total"])

    def get_random_manga(self) -> Manga | None:
        """Fetches a random manga from the `GET /manga/random` endpoint."""
        endpoint = f"{self.cfg.reqs.api_root}/manga/random"
        r_json = self._safe_get_json(endpoint)

        return Manga(
            self._get_title(r_json["data"]["attributes"]), r_json["data"]["id"]
        )
