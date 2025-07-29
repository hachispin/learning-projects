"""Stores classes used to handle menus"""

# pylint:disable=unused-import
from dataclasses import dataclass
from enum import Enum, auto
import sys
import time
import logging

from requests import session

from mdex_dl.api.search import Searcher
from mdex_dl.cli.ansi.output import AnsiOutput
from mdex_dl.cli.controls.classes import Control, ControlGroup
from mdex_dl.models import Config, SearchResults
from mdex_dl.cli.utils import CliUtils
from mdex_dl.api.http_config import get_retry_adapter
from mdex_dl.cli.controls.constants import (
    BACK,
    DOWNLOAD,
    MAIN_MENU_CONTROLS,
    PAGE_CONTROLS,
    QUIT,
    SEARCH,
)

logger = logging.getLogger(__name__)


class Menu:
    """
    A menu where users can navigate to and from.

    NOTE: This should not be used as it's own class, but
    instead as an interface (abstract base class).
    """

    _USE_GETCH = True

    # These options should **always** be overriden
    _DESCRIPTION = "_OVERRIDE_ME_"
    _CG = ControlGroup((Control("?", "?"),))

    def __init__(self, cfg: Config):
        self.keys = {c.key for c in self._CG.controls}
        self.cfg = cfg
        self.utils = CliUtils(cfg)
        self.ansi = AnsiOutput(cfg.cli)

    def _show_controls(self):
        """
        Prints all controls with equal spacing and according
        to `config.cli.options_per_row`

        Args:
            cg (ControlGroup): the controls to be printed
        """
        # if it's just one row
        if len(self._CG.controls) <= self.cfg.cli.options_per_row:
            print(" ".join([c.label for c in self._CG.controls]))
            return

        options_per_row = self.cfg.cli.options_per_row
        labels = tuple(c.label for c in self._CG.controls)
        max_len = max(len(l) for l in labels)

        for idx, l in enumerate(labels):
            spacing = (max_len + 1) - len(l)

            if (idx + 1) % options_per_row == 0:  # New row
                print(l)
            else:  # Stay on current
                print(l, end=" " * spacing)

        if len(labels) % options_per_row != 0:
            print()  # Newline at end of options if not already printed

    def show(self):
        """Prints the menu's description and controls."""
        if self._DESCRIPTION:
            print(self._DESCRIPTION)
        self._show_controls()

    def get_option(self) -> str:
        """Gets a validated option from the user."""
        while True:
            self.utils.clear()
            self.show()
            if self._USE_GETCH:
                user_input = self.utils.get_input_key()
            else:
                user_input = input().strip().upper()

            if user_input in self.keys:
                return user_input

            print(self.ansi.to_err("\nInvalid input"))
            time.sleep(self.cfg.cli.time_to_read)

    def handle_option_defaults(self, option: str) -> "MenuAction":
        """
        Handles defaults such as the `BACK` and `QUIT` keys.
        """
        if option == QUIT.key:
            sys.exit(0)
        if option == BACK.key:
            return MenuAction(None, Action.POP)
        return MenuAction(None, Action.NONE)

    def handle_option(self, option: str):
        """
        Handles all non-default options.

        `handle_option_defaults()` should be called after this.
        """
        raise NotImplementedError("handle_option() not implemented in child class.")


class Action(Enum):
    """Stores the enums used for communication between Menu and MenuStack."""

    PUSH = auto()
    POP = auto()
    NONE = auto()


@dataclass
class MenuAction:
    """Used by MenuStack to perform stack actions such as pushing."""

    menu: Menu | None
    action: Action

    def __post_init__(self):
        if self.menu is None and self.action == Action.PUSH:
            raise ValueError("Expected menu to push, got None")


class MenuStack:
    """A stack of Menu instances."""

    def __init__(self, menus: list[Menu]):
        self.menus = menus

    def pop(self) -> Menu | None:
        """Removed the Menu at the top of the stack."""
        if self.menus:
            return self.menus.pop()
        return None

    def push(self, menu: Menu) -> None:
        """Adds a Menu to the top of the stack."""
        self.menus.append(menu)

    def peek(self) -> Menu | None:
        """Returns the Menu at the top of the stack if it exists, else None"""
        if self.menus:
            return self.menus[-1]
        return None

    def handle_action(self, menu_action: MenuAction):
        """Handles MenuAction instances returned by Menu subclasses."""
        match menu_action.action:
            case Action.PUSH:
                self.push(menu_action.menu)  # type: ignore
            case Action.POP:
                self.pop()
            case Action.NONE:
                pass
            case _:
                raise ValueError(f"Unknown action '{menu_action.action}'")


# Menu subclasses
class MainMenu(Menu):
    """The menu shown upon startup."""

    _DESCRIPTION = "What to do?"
    _CG = MAIN_MENU_CONTROLS

    def handle_option(self, option: str) -> MenuAction:
        match option:
            case SEARCH.key:
                return MenuAction(SearchMenu(self.cfg), Action.PUSH)
            case DOWNLOAD.key:
                return MenuAction(DownloadMenu(self.cfg), Action.PUSH)

        return super().handle_option_defaults(option)


class SearchMenu(Menu):
    """Searches for the user's query and redirects results to ResultsMenu."""

    _USE_GETCH = False
    _DESCRIPTION = "Search for a manga's title or enter ':B' to go back"

    def __init__(self, cfg):
        self.searcher = Searcher(cfg)
        super().__init__(cfg)

    def get_option(self) -> str:
        return input(">> ").strip()

    def handle_option(self, option: str) -> MenuAction:
        if option.upper() == ":B":
            return MenuAction(None, Action.POP)

        res = self.searcher.search(query=option, page=0)
        return


class ResultsMenu(Menu):
    """Displays and allows access to paginated results of a search query."""

    _USE_GETCH = False
    _DESCRIPTION = (
        "Choose a manga's number, on the left, or enter one of these options:"
    )
    _CG = PAGE_CONTROLS

    def __init__(self, first_page: SearchResults, cfg: Config):
        # off-by-one is intentional here because of first page
        total_pages = first_page.total // cfg.search.results_per_page
        self.searches = [first_page]  # type: list[SearchResults | None]
        self.searches.extend([None] * total_pages)

        super().__init__(cfg)


class DownloadMenu(Menu): ...


if __name__ == "__main__":
    # pylint:disable= wildcard-import unused-wildcard-import
    from mdex_dl.load_config import *

    test_config = Config(
        reqs=ReqsConfig(
            api_root="https://api.mangadex.org",
            report_endpoint="https://api.mangadex.network/report",
            get_timeout=10,
            post_timeout=20,
        ),
        save=SaveConfig(location="mdex_save", max_title_length=60),
        retry=RetryConfig(
            max_retries=5, backoff_factor=1, backoff_jitter=0.5, backoff_max=30
        ),
        images=ImagesConfig(use_datasaver=False),
        search=SearchConfig(results_per_page=10, include_pornographic=False),
        cli=CliConfig(options_per_row=3, use_ansi=True, time_to_read=1),
        logging=LoggingConfig(enabled=True, level=20, location="logs"),
    )
    main_menu = MainMenu(test_config)
    nav = MenuStack([main_menu])
    current = nav.peek()
    assert current is not None
    current.show()
    print(current.get_option())
