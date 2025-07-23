"""
The entry-point of this project. This is also the only module
where `mdex_dl.load_config` is used. All other modules then
inherit the config from here.
"""

from enum import Enum
import logging
import sys

from requests import session

from mdex_dl.api.client import get_manga_feed
from mdex_dl.api.http_config import get_retry_adapter
from mdex_dl.api.search import Searcher
from mdex_dl.api.download import Downloader
from mdex_dl.models import Manga, Chapter
from mdex_dl.load_config import require_ok_config
from mdex_dl.logger import setup_logging


cfg = require_ok_config()
setup_logging(cfg.logging)
logger = logging.getLogger(__name__)

logger.debug("Hello, world!")

# Create retry session
main_session = session()
adapter = get_retry_adapter(cfg.retry)
main_session.mount("http://", adapter)
main_session.mount("https://", adapter)


class Controls(Enum):
    """The CLI controls displayed for actions such as searching"""

    SEARCH = ("[Q] Prev", "[E] Next", "[Enter] Search again")
    MANGA = ("[D]ownload", "[V]iew info", "[B]ack")
    SEARCH_KEYS = ("Q", "E", "")
    MANGA_KEYS = ("D", "V", "B")


def print_options(*options: str):
    """Prints all options with equal spacing and linebreaking"""
    options_per_row = cfg.cli.options_per_row
    max_len = max(len(option) for option in options)

    for idx, opt in enumerate(options):
        spacing = (max_len + 1) - len(opt)

        if (idx + 1) % options_per_row == 0:  # New row
            print(opt)
        else:  # Stay on current
            print(opt, end=" " * spacing)

    if len(options) % options_per_row != 0:
        print()  # Newline at end of options if not already printed


def print_manga_names(manga: tuple[Manga, ...]):
    """Prints manga names with a left index for use by the user"""
    for idx, m in enumerate(manga):
        print(f"[{idx+1}]: {m.title}")


def input_int(prompt: str, maximum: int, minimum: int = 0) -> int:
    """WIP"""
    while True:
        user_input = input(prompt).upper()

        if user_input == "X":
            sys.exit(0)
        elif not user_input.isdigit():
            print("Not a number")
        elif not minimum <= int(user_input) <= maximum:
            print("Outside range")
        else:
            return int(user_input)


if __name__ == "__main__":
    s = Searcher(cfg)

    while True:
        query = input("Search something: ")
        res = s.search(query, page=0)
        print_manga_names(res.results)
        chosen_manga = res.results[input_int("Enter index: ", 10) - 1]

        chosen_chapters = get_manga_feed(main_session, cfg, chosen_manga)["data"]

        if not chosen_chapters:
            print("No available chapters. Try again :)")
            continue

        for c in chosen_chapters:
            if c["attributes"]["translatedLanguage"] != "en":
                continue
            chapter = Chapter(c["id"], c["attributes"]["chapter"])
            d = Downloader(chosen_manga, chapter, cfg)
            d.download_images()

        break
