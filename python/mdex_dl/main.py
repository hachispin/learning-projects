"""
The entry-point of this project. This is also the only module
where `mdex_dl.load_config` is used. All other modules then
inherit the config from here.
"""

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


def print_controls(cg: ControlGroup) -> None:
    """
    Prints all controls with equal spacing and according
    to `config.cli.options_per_row`

    Args:
        cg (ControlGroup): the controls to be printed
    """
    # if it's just one row
    if len(cg.controls) <= cfg.cli.options_per_row:
        print(" ".join([c.label for c in cg.controls]))
        return

    options_per_row = cfg.cli.options_per_row
    labels = tuple(c.label for c in cg.controls)
    max_len = max(len(l) for l in labels)

    for idx, l in enumerate(labels):
        spacing = (max_len + 1) - len(l)

        if (idx + 1) % options_per_row == 0:  # New row
            print(l)
        else:  # Stay on current
            print(l, end=" " * spacing)

    if len(labels) % options_per_row != 0:
        print()  # Newline at end of options if not already printed

    return


def print_manga_titles(manga: tuple[Manga, ...]):
    """Prints manga titles with a left index for use by the user."""
    for idx, m in enumerate(manga):
        print(f"[{idx+1}]: {m.title}")


def print_chapter_titles(chapters: tuple[Chapter, ...]):
    """Prints chapter titles with a left index for use by the user."""
    for idx, c in enumerate(chapters):
        print(f"[{idx+1}]: {c.title}")


logger.debug("User platform: %s", sys.platform)
if sys.platform == "win32":

    def clear():
        """Clears the terminal."""
        os.system("cls")

else:

    def clear():
        """Clears the terminal."""
        os.system("clear")


def get_input_key() -> str:
    """Normalises input to be compared against uppercase Control.key values."""
    print(">> ", flush=True, end="")
    option = getch().upper()
    print(option)
    return option


def get_option(cg: ControlGroup, message: str | None = None) -> str:
    """
    Gets a validated option from the user.

    Args:
        message (str): the text displayed before controls are shown
        cg (ControlGroup): the controls to display and look for

    Returns:
        str: the key entered by the user
    """
    allowed = tuple(c.key for c in cg.controls)
    while True:
        clear()
        if message:
            print(message + "\n")
        print_controls(cg)
        user_input = get_input_key()

        if user_input == QUIT.key:
            sys.exit(0)
        if user_input in allowed:
            return user_input

        print(ansi.to_err("[Invalid option]"))
        time.sleep(cfg.cli.time_to_read)


# getch() isn't used here since manga indices can be two characters (e.g. "10")
def get_page_option(
    res: SearchResults,
    current_page: int,
    total_pages: int,
    last_index: int = cfg.search.results_per_page,
) -> str:
    """
    Gets a valid page option or manga index from the user.

    This also prints the
    necessary information needed for the user to choose their option.

    Args:
        last_index (int, optional): the last index that the user can pick.
            **This should be one-indexed** as the index is user-facing.

            Defaults to cfg.search.results_per_page.

    Returns:
        str: the validated option the user picked; may be a manga index or
            a page control.
    """
    allowed = [c.key for c in PAGE_CONTROLS.controls]
    allowed += list(str(i) for i in range(1, last_index + 1))
    total_pages = (res.total // cfg.search.results_per_page) + 1

    while True:
        clear()

        print_manga_titles(res.results)
        print(ansi.to_inverse(f"Page {current_page+1} / {total_pages}\n"))
        print("Type the manga's number on the left to select, or:")
        print_controls(PAGE_CONTROLS)

        user_input = input(">> ").upper()
        if user_input == QUIT.key:
            sys.exit(0)
        if user_input in allowed:
            return user_input
        # failure cases
        if user_input.isdigit():
            print(ansi.to_err("[Invalid manga index]"))
        else:
            print(ansi.to_err("[Invalid page control]"))

        time.sleep(cfg.cli.time_to_read)


# Menus
# - NOTE: QUIT.key should be checked for in the input validator.
# pylint:disable=missing-function-docstring
searcher = Searcher(cfg)
ansi = AnsiOutput(cfg.cli)  # for ANSI formatted messages


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


def is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


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

    ordered = []
    unordered = []

    for c in chapters:
        if c.chap_num is not None and is_float(c.chap_num):
            ordered.append(c)
        else:
            unordered.append(c)

    ordered.sort(key=lambda c: float(c.chap_num))  # type: ignore
    chapters = ordered + unordered

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
