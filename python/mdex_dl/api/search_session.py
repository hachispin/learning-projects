"""
Contains the SearchSession class, which is used to handle pagination and
search caching of queries.
"""

from mdex_dl.api.search import Searcher
from mdex_dl.models import Config, SearchResults


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
        first_page: SearchResults,
        cfg: Config,
    ):
        self._page = 0
        self._query = query
        self.searcher = searcher

        self.total_pages = first_page.total // cfg.search.results_per_page + 1
        self.pages = [first_page]  # type: list[SearchResults | None]
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

    def load_page(self) -> SearchResults:
        """
        Returns the SearchResults of the current page.

        This checks if the page is already cached before fetching it from
        MangaDex.

        Args:
            page (int): the page index to access

        Raises:
            IndexError: if the page index is out of range

        Returns:
            SearchResults: the results of the given page
        """
        if not 0 <= self.page < len(self.pages):
            raise IndexError(f"Page index {self.page} out of range")
        if self.pages[self.page] is not None:
            return self.pages[self.page]  # type: ignore

        res = self.searcher.search(self.query, self.page)
        self.pages[self.page] = res
        return res
