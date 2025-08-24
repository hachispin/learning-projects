"""
Contains the SearchSession class, which is used to handle pagination and
search caching of queries.
"""

from itertools import batched
import logging
from typing import Any

from mdex_tool.api.client import safe_get_json
from mdex_tool.api.http_config import get_retry_session
from mdex_tool.api.search import Searcher
from mdex_tool.models import Chapter, Config, Manga, MangaResults

logger = logging.getLogger(__name__)


class MangaPaginator:
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


class ChapterPaginator:
    """
    A paginator for manga feed (chapters of a manga). This is created per-manga.

    Unlike SearchSession, this does not use lazy loading; all chapters
    are fetched upon creation and then paginated internally for UX.
    """

    def __init__(self, manga: Manga, cfg: Config):
        self.session = get_retry_session(cfg.retry)
        self.manga = manga
        self.cfg = cfg

        chapters = self.get_manga_feed()
        self.pages = tuple(batched(chapters, self.cfg.search.results_per_page))
        self.total_pages = len(self.pages)
        self._page = 0

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

    def _format_chapter_titles(
        self, chapter_data: list[dict[str, Any]]
    ) -> tuple[Chapter, ...]:
        """Zero-pads chapter titles and gives unknown chapter titles more info."""
        chapters = []  # type: list[Chapter]

        def is_float_coercible(x) -> bool:
            try:
                float(x)
                return True
            except (ValueError, TypeError):
                return False

        unknown_idx = 1  # to prevent naming conflicts
        zeros = len(str(len(chapter_data)))
        for cd in chapter_data:
            uuid = cd["id"]
            chap_num = cd["attributes"]["chapter"]
            chapter = Chapter(uuid, chap_num)

            if is_float_coercible(chap_num) and "." in chap_num:
                left, sep, right = chap_num.partition(".")
                # ljust to zeropad decimal part; e.g. 0.1 -> 0.10
                padded = left.zfill(zeros) + sep + right.ljust(2, "0")
                chapter.title = f"Ch. {padded}"
                chapters.append(chapter)
                continue

            if is_float_coercible(chap_num):  # int-like
                chapter.title = f"Ch. {str(chap_num).zfill(zeros)}"
                chapters.append(chapter)
                continue

            # try to gather more info
            # example:
            #   Ch. Unknown #3 (title: 'Special')
            title = cd["attributes"]["title"]
            chapter.title += f" #{str(unknown_idx).zfill(zeros)}"

            if isinstance(title, str) and title.strip():
                chapter.title += f" (title: '{title}')"

            unknown_idx += 1
            chapters.append(chapter)

        return tuple(chapters)

    def get_manga_feed(self) -> tuple[Chapter, ...]:
        """
        Sends a GET request to the `GET /manga/manga.id/feed` endpoint.

        **This fetches ALL chapters** using the largest allowed pagination
        by MangaDex (500).

        Returns:
            (tuple[Chapter, ...]): all chapters of the manga
        """
        feed = f"{self.cfg.reqs.api_root}/manga/{self.manga.uuid}/feed"
        chapter_data = []  # type: list[dict[str, Any]]

        # 18+ filtering should be done upstream in the Searcher class
        params = {
            "translatedLanguage[]": ["en"],
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"],
            "order[chapter]": "asc",
            "includeEmptyPages": 0,
            "limit": 500,  # the max that MangaDex allows
            "offset": 0,
        }  # type: dict[str, Any]

        # Keep fetching until no results
        while True:
            if params["offset"] >= 9500:
                logger.warning("Max pagination reached (offset + limit) > 10'000")
                break

            logger.info(
                "Fetching chapters for '%s', page=%s",
                self.manga.title,
                params["offset"] // 500,
            )

            r_json = safe_get_json(feed, self.session, self.cfg, params)
            logger.debug(  # this produces overhead; keep the dict comp here
                "Pagination info: %s", {k: v for k, v in r_json.items() if k != "data"}
            )

            if not r_json["data"]:
                logger.info("Received blank data; fetching stopped")
                break

            chapter_data += r_json["data"]
            params["offset"] += 500

        return self._format_chapter_titles(chapter_data)

    def load_page(self) -> tuple[Chapter, ...]:
        """Returns the chapters at the current page."""
        return self.pages[self.page]
