"""
The entry-point of this project. This is also the only module
where `mdex_dl.load_config` is used. All other modules then
inherit the config from here.
"""

from enum import Enum
import logging

from mdex_dl.api.search import search_manga
from mdex_dl.models import Manga  # from mdex_dl.api.download import Downloader
from mdex_dl.load_config import require_ok_config
from mdex_dl.logger import setup_logging


config = require_ok_config()
setup_logging(config)
logger = logging.getLogger(__name__)
OPTIONS_PER_ROW = config["cli"]["options_per_row"]

logger.debug("Hello, world!")


class Controls(Enum):
    """The CLI controls displayed for actions such as searching"""

    SEARCH = ("[Q] Prev", "[E] Next", "[Enter] Search again")
    MANGA = ("[D]ownload", "[V]iew info", "[B]ack")


def print_options(*options: str):
    """Prints all options with equal spacing and linebreaking"""
    max_len = max(len(option) for option in options)

    for idx, option in enumerate(options):
        spacing = (max_len + 1) - len(option)

        if (idx + 1) % OPTIONS_PER_ROW == 0:  # New row
            print(option)
        else:  # Stay on current
            print(option, end=" " * spacing)

    if len(options) % OPTIONS_PER_ROW != 0:
        print()  # Newline at end of options if not already printed


def print_manga_names(manga: list[Manga]):
    """Prints manga names with a left index for use by the user"""
    for idx, m in enumerate(manga):
        print(f"[{idx+1}]: {m.title}")


page = 0

while True:
    search = input("Search for a manga name in Romaji: ")
    results = search_manga(search, page)  # list[Manga]
    print_manga_names(results)
    print_options(*Controls.MANGA.value, "[X] Close program")
