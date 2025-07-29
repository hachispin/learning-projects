"""
The entry-point of this project. This is also the only module
where `mdex_dl.load_config` is used. All other modules then
inherit the config from here.
"""

if __name__ == "__main__":
    raise RuntimeError("run me as a module with the -m flag :)")

import logging
import os
import sys
import time

from requests import session


# API; Requests
from mdex_dl.api.client import get_manga_feed
from mdex_dl.api.http_config import get_retry_adapter
from mdex_dl.api.search import Searcher
from mdex_dl.api.download import Downloader

# API; Data structures
from mdex_dl.models import Manga, Chapter, SearchResults

# Config/Logging
from mdex_dl.load_config import require_ok_config
from mdex_dl.logger import setup_logging

# CLI
from mdex_dl.cli.controls.constants import (
    BACK,
    DOWNLOAD,
    LAST_PAGE,
    NEXT_PAGE,
    QUIT,
    MAIN_MENU_CONTROLS,
    PAGE_CONTROLS,
    MANGA_CONTROLS,
    SEARCH,
    VIEW_INFO,
)
from mdex_dl.cli.controls.classes import ControlGroup
from mdex_dl.cli.ansi.output import AnsiOutput, ProgressBar
from mdex_dl.cli.getch import getch  # type: ignore

cfg = require_ok_config()
setup_logging(cfg.logging)
logger = logging.getLogger(__name__)

# Create retry session
main_session = session()
adapter = get_retry_adapter(cfg.retry)
main_session.mount("http://", adapter)
main_session.mount("https://", adapter)

logger.debug("Hello, world!")
logger.debug("User platform: %s", sys.platform)


def main_menu() -> None:
    user_input = get_option(MAIN_MENU_CONTROLS)

    match user_input:
        case SEARCH.key:
            start_search()
        case DOWNLOAD.key:
            download_from_link_menu()
        case _:
            logger.error("Invalid key passed from get_option() to main_menu")
            main_menu()


def download_from_link_menu() -> None: ...


def start_search() -> None:
    clear()
    user_query = input("Search MangaDex: ")
    res = searcher.search(user_query)
    logger.debug(repr(res))

    if res.total == 0 or len(res.results) == 0:
        print(ansi.to_warn("No results found"))
        time.sleep(cfg.cli.time_to_read)
        start_search()

    page_menu(user_query, res, 0)


def page_menu(user_query: str, res: SearchResults, page: int) -> None:
    total_pages = (res.total // cfg.search.results_per_page) + 1
    user_input = get_page_option(res, page, total_pages)

    if user_input.isdigit():
        manga_menu(res.results[int(user_input) - 1])

    match user_input:
        case LAST_PAGE.key:
            page -= 1
            page = page % total_pages
            page_menu(user_query, searcher.search(user_query, page), page)
        case NEXT_PAGE.key:
            page += 1
            page = page % total_pages
            page_menu(user_query, searcher.search(user_query, page), page)
        case BACK.key:
            main_menu()
        case _:
            raise ValueError()


def manga_menu(manga: Manga) -> None:
    user_input = get_option(
        MANGA_CONTROLS,
        message=f"Chosen manga: {ansi.to_underline(manga.title)}",
    )

    match user_input:
        case DOWNLOAD.key:
            download_manga_menu(manga)
        case VIEW_INFO.key:
            raise NotImplementedError()
        case BACK.key:
            start_search()


def download_manga_menu(manga: Manga) -> None:
    feed = get_manga_feed(main_session, cfg, manga)
    total_chapters = feed["total"]
    logger.info("Found chapters: %s", total_chapters)
    logger.debug("Feed: %s", feed)

    chapters = [
        Chapter(c["id"], c["attributes"]["chapter"])
        for c in feed["data"]
        if c["attributes"]["pages"] != 0
    ]  # type: list[Chapter]

    # Seperate into valid and invalid chapter numbers

    ordered = []  # type: list[Chapter]
    unordered = []  # type: list[Chapter]

    for c in chapters:
        if c.chap_num is not None and is_float(c.chap_num):
            ordered.append(c)
        else:
            unordered.append(c)

    # Index unordered chapter titles to prevent naming conflicts
    for i, c in enumerate(unordered):
        c.title = f"{c.title} [{i}]"

    ordered.sort(key=lambda c: float(c.chap_num))  # type: ignore
    chapters = ordered + unordered  # unordered goes to last page

    if not chapters:
        print(ansi.to_warn("No available chapters found"))
        start_search()

    print_chapter_titles(tuple(chapters))

    chapter_range = input("Enter a range of chapters: ")
    start, end = chapter_range.split("-")

    for i in range(int(start) - 1, int(end)):
        pb = ProgressBar(cfg.cli, f"Downloading [{i+1}]")
        dl = Downloader(manga, chapters[i], cfg)

        dl.download_images(progress_out=pb.display)

    print(ansi.to_success("Download complete"))
    time.sleep(cfg.cli.time_to_read)
    main_menu()


def main():
    """The entry point  ヾ(•ω•`)o"""
    main_menu()


if __name__ == "__main__":
    main()
