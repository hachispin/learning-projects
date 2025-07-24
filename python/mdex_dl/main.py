"""
The entry-point of this project. This is also the only module
where `mdex_dl.load_config` is used. All other modules then
inherit the config from here.
"""

# pylint: disable=unused-import

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
from mdex_dl.models import Manga, Chapter

# Config/Logging
from mdex_dl.load_config import require_ok_config
from mdex_dl.logger import setup_logging

# CLI
from mdex_dl.cli.controls.constants import (
    MAIN_MENU_CONTROLS,
    PAGE_CONTROLS,
    MANGA_CONTROLS,
)
from mdex_dl.models import Control, ControlGroup
from mdex_dl.ansi.output import AnsiOutput


cfg = require_ok_config()
setup_logging(cfg.logging)
logger = logging.getLogger(__name__)


ansi = AnsiOutput(cfg.cli)  # for ANSI formatted messages

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


def print_manga_names(manga: tuple[Manga, ...]):
    """Prints manga names with a left index for use by the user"""
    for idx, m in enumerate(manga):
        print(f"[{idx+1}]: {m.title}")


if os.name == "nt":

    def clear():
        """Clears the terminal."""
        os.system("cls")

else:

    def clear():
        """Clears the terminal."""
        os.system("clear")


def get_input_key() -> str:
    """Normalises input to be compared against uppercase Control.key values."""
    return input(">> ").upper()


def get_option(cg: ControlGroup) -> str:
    """
    Gets a validated option from the user.

    Args:
        prompt (str): the message displayed on the input field
        cg (ControlGroup): the controls to display and look for

    Returns:
        str: the key entered by the user
    """
    allowed = tuple(c.key for c in cg.controls)
    while True:
        clear()
        print_controls(cg)
        user_input = get_input_key()

        if user_input == "X":
            sys.exit(0)
        if user_input in allowed:
            return user_input

        ansi.print_err("[Invalid option]")
        time.sleep(1)  # to give time for the user to read before clearing


# Menus
# pylint:disable=missing-function-docstring


def main_menu() -> None:
    user_input = get_option(MAIN_MENU_CONTROLS)

    match user_input:
        case "S":
            page_menu()
        case "D":
            raise NotImplementedError("gotta wait bud")
        case _:
            raise ValueError("How did you get here?")


def page_menu() -> None: ...


def main():
    """The entry point. ヾ(•ω•`)o"""
    main_menu()


if __name__ == "__main__":
    main()
