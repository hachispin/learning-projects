"""
Contains the SearchSession class, which is used to handle pagination and
search caching of queries.
"""

from itertools import batched
import logging
from typing import Any

import requests

from mdex_dl.api.client import safe_get_json
from mdex_dl.api.search import Searcher
from mdex_dl.models import Chapter, Config, Manga, MangaResults

logger = logging.getLogger(__name__)


class SearchSession:
    """
    Handles pagination and caching for a given query.

    NOTE: SearchSession is created per-query. i.e. you shouldn't mutate
    self._query.
    """

    def __init__(
        self,
        query: str,
        searcher: Searcher,
        first_page: MangaResults,
        cfg: Config,
    ):
        self._page = 0
        self._query = query
        self.searcher = searcher

        page_limit = cfg.search.results_per_page
        self.total_pages = (first_page.total + page_limit - 1) // page_limit
        self.pages = [first_page]  # type: list[MangaResults | None]
        self.pages.extend([None] * (self.total_pages - 1))

    # pylint:disable=missing-function-docstring
    @property
    def query(self) -> str:
        return self._query

    @property
    def page(self) -> int:
        return self._page

    # pylint:enable=missing-function-docstring
    @page.setter
    def page(self, value: int):
        # wraparound
        self._page = value % self.total_pages

    def load_page(self) -> MangaResults:
        """
        Returns the MangaResults of the current page.

        This checks if the page is already cached before fetching it from
        MangaDex.

        Args:
            page (int): the page index to access

        Raises:
            IndexError: if the page index is out of range

        Returns:
            MangaResults: the results of the given page
        """
        if not 0 <= self.page < len(self.pages):
            raise IndexError(f"Page index {self.page} out of range")
        if self.pages[self.page] is not None:
            return self.pages[self.page]  # type: ignore

        res = self.searcher.search(self.query, self.page)
        self.pages[self.page] = res
        return res


class MangaFeed:
    """
    A paginator for manga feed (chapters of a manga). This is created per-manga.

    Unlike SearchSession, this does not use lazy loading; all chapters
    are fetched upon creation and then paginated internally for UX.
    """

    def __init__(self, session: requests.Session, manga: Manga, cfg: Config):
        self.session = session
        self.manga = manga
        self.cfg = cfg

        chapters = self.get_manga_feed()
        self.pages = tuple(batched(chapters, self.cfg.search.results_per_page))
        self.total_pages = len(self.pages)

    # These properties are the same as SearchSession but
    # this class is too different to be a subclass

    # pylint:disable=missing-function-docstring

    @property
    def page(self) -> int:
        return self._page

    # pylint:enable=missing-function-docstring
    @page.setter
    def page(self, value: int):
        # wraparound
        self._page = value % self.total_pages

    def get_manga_feed(self) -> tuple[Chapter, ...]:
        """
        Sends a GET request to the `GET /manga/manga.id/feed` endpoint.

        **This fetches ALL chapters** using the largest allowed pagination
        by MangaDex (500).

        The chapters returned (through `ChapterResults`) are also
        sanitised through the helper function clean_manga_feed().

        Args:
            session (requests.Session): the client used to send request
            manga (Manga): the manga to fetch chapters from
            cfg (Config): the config used

        Returns:
            ChapterResults: a tuple of chapters
        """
        feed = f"{self.cfg.reqs.api_root}/manga/{self.manga.uuid}/feed"
        offset = 0
        chapter_data = []  # type: list[dict[str, Any]]

        # 18+ filtering should be done upstream in the Searcher class
        params = {
            "translatedLanguage[]": ["en"],
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
            "order[chapter]": "asc",
            "includeEmptyPages": 0,
            "limit": 500,  # the max that MangaDex allows
            "offset": offset,
        }

        # Keep fetching until no results
        while True:
            if offset >= 9500:
                logger.warning("Max pagination reached (offset + limit) > 10'000")
                break

            logger.info(
                "Fetching chapters for '%s', page=%s", self.manga.title, offset // 500
            )
            r_json = safe_get_json(feed, self.session, self.cfg, params)
            r_json_no_data = {k: v for k, v in r_json.items() if k != "data"}
            logger.debug("Pagination info: %s", r_json_no_data)

            if not r_json["data"]:
                break

            chapter_data += r_json["data"]
            offset += 500
            params["offset"] = offset

        return tuple(
            Chapter(cd["id"], cd["chapter"])
            for cd in chapter_data
            if cd["attributes"]["externalUrl"] is None
        )  # ^ if chapter is readable on MangaDex

    def load_page(self) -> tuple[Chapter, ...]:
        """Returns the chapters at the current page."""
        return self.pages[self.page]
