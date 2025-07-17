from mdex_dl.api.search import search_manga
from mdex_dl.api.download import Downloader

from mdex_dl.models import Manga
import tomli
from pathlib import Path


with open("config.toml", "rb") as f:
    config = tomli.load(f)

OPTIONS_PER_ROW = config["cli"]["options_per_row"]


class Controls:
    SEARCH = ("[Q] Prev", "[E] Next", "[Enter] Search again")
    MANGA = ("[D]ownload", "[V]iew info", "[B]ack")


def print_options(*options: str):
    max_len = max(len(option) for option in options)

    for idx, option in enumerate(options):
        spacing = (max_len + 1) - len(option)

        if (idx + 1) % OPTIONS_PER_ROW == 0:  # New row
            print(option)
        else:  # Stay on current
            print(option, end=" "*spacing)

    if len(options) % OPTIONS_PER_ROW != 0:
        print()  # Newline at end of options if not already printed


def print_manga_names(manga: list[Manga]):
    for idx, m in enumerate(manga):
        print(f"[{idx+1}]: {m.title}")


page = 0

while True:
    search = input("Search for a manga name in Romaji: ")
    results = search_manga(search, page)  # list[Manga]
    print_manga_names(results)
    print_options(*Controls.MANGA, "[X] Close program")
