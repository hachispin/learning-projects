"""Stores classes used to handle menus"""

from dataclasses import dataclass
from enum import Enum, auto
import sys
import textwrap
import time
import logging

from mdex_tool.models import Config, Manga, MangaResults
from mdex_tool.api.search import Searcher
from mdex_tool.api.pagination import ChapterPaginator, MangaPaginator
from mdex_tool.cli.ansi.output import AnsiOutput
from mdex_tool.cli.utils import CliUtils
from mdex_tool.cli.controls.classes import Control, ControlGroup
from mdex_tool.cli.controls.constants import (
    BACK,
    DOWNLOAD,
    HELP,
    PREV_PAGE,
    MAIN_MENU_CONTROLS,
    MANGA_CONTROLS,
    NEXT_PAGE,
    PAGE_CONTROLS,
    PAGE_CONTROLS_CHAPTERS,
    QUIT,
    SEARCH,
    VIEW_INFO,
)


logger = logging.getLogger(__name__)


class Menu:
    """
    A menu where users can navigate to and from.

    NOTE: This should not be used as it's own class, but
    instead as an interface (abstract base class).
    """

    USE_GETCH = True

    # These options should **always** be overriden
    CG = ControlGroup((Control("Unknown control", "?"),))
    description = "_OVERRIDE_ME_"

    def __init__(self, cfg: Config):
        self.keys = {c.key for c in self.CG.controls}
        self.cfg = cfg
        self.utils = CliUtils(cfg)
        self.ansi = AnsiOutput(cfg.cli)

    def _show_controls(self):
        """
        Prints all the controls within `self.CG` with equal
        spacing and according to `config.cli.options_per_row`
        """
        # if it's just one row
        if len(self.CG.controls) <= self.cfg.cli.options_per_row:
            print("  ".join([c.label for c in self.CG.controls]))
            return

        options_per_row = self.cfg.cli.options_per_row
        labels = tuple(c.label for c in self.CG.controls)
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
        """
        Prints the menu's description and controls.

        Subclasses should override this to clear the terminal.
        This isn't present in the superclass to allow for flexibility.
        """
        if self.description:
            print(self.description + "\n")
        self._show_controls()

    def get_option(self) -> str:
        """Gets a validated option from the user."""
        while True:
            self.utils.clear()
            self.show()
            if self.USE_GETCH:
                user_input = self.utils.get_input_key()
            else:
                user_input = input(">> ").strip().upper()

            logger.debug(
                "User input '%s' from class: %s", user_input, type(self).__name__
            )

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

    def handle_option(self, option: str) -> "MenuAction":
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
        logger.debug(
            "Received MenuAction: %s, %s",
            type(menu_action.menu).__name__,
            menu_action.action.name,
        )
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

    CG = MAIN_MENU_CONTROLS
    description = textwrap.dedent(
        """\
        Welcome!
        
        Guide: enter the bracketed key to perform the labeled action.
        e.g. "[Q] Quit" means that if you enter "Q", the program will
        exit!
        
        Enter an action key:\
        """
    )

    def show(self):
        self.utils.clear()
        super().show()

    def handle_option(self, option: str) -> MenuAction:
        if option == SEARCH.key:
            return MenuAction(SearchMenu(self.cfg), Action.PUSH)
        if option == DOWNLOAD.key:
            raise NotImplementedError("WIP")

        return self.handle_option_defaults(option)


class SearchMenu(Menu):
    """Searches for the user's query and redirects results to ResultsMenu."""

    USE_GETCH = False
    description = "Search for a manga's title or enter ':B' to go back"

    def __init__(self, cfg):
        self.searcher = Searcher(cfg)
        super().__init__(cfg)

    def show(self):
        self.utils.clear()
        print(self.description)

    def get_option(self) -> str:
        return input(">> ").strip()

    def handle_option(self, option: str) -> MenuAction:
        if option.upper() == ":B":
            return MenuAction(None, Action.POP)

        res = self.searcher.search(query=option, page=0)

        if not res.results:
            print(self.ansi.to_warn("No manga found"))
            time.sleep(self.cfg.cli.time_to_read)
            return MenuAction(None, Action.NONE)

        return MenuAction(
            ResultsMenu(self.searcher, option, res, self.cfg),
            Action.PUSH,
        )


class ResultsMenu(Menu):
    """
    Displays and allows access to paginated results of a search query.

    Note that the manga index chosen by the user is one-indexed.
    """

    CG = PAGE_CONTROLS
    description = (
        "Choose a manga's number, on the left, or enter one of these action keys:"
    )

    def __init__(
        self,
        searcher: Searcher,
        query: str,
        first_page: MangaResults,
        cfg: Config,
    ):
        if cfg.search.results_per_page >= 10:
            self.USE_GETCH = False  # pylint:disable=invalid-name

        self.ss = MangaPaginator(query, searcher, first_page, cfg)
        super().__init__(cfg)

    def show(self):
        self.utils.clear()
        page = self.ss.load_page()
        self.utils.print_manga_titles(page.results)
        print(
            self.ansi.to_inverse(f"  Page {self.ss.page + 1}/{self.ss.total_pages}  ")
        )
        super().show()

    def get_option(self) -> str:
        max_manga_index = len(self.ss.load_page().results)
        allowed = self.keys.union({str(i) for i in range(1, max_manga_index + 1)})

        while True:
            option = input(">> ").strip().upper()
            if option not in allowed:
                print(self.ansi.to_err("\nInvalid input"))
                time.sleep(self.cfg.cli.time_to_read)
                self.show()
            else:
                return option

    def handle_option(self, option: str) -> MenuAction:
        if option == NEXT_PAGE.key:
            self.ss.page += 1
            self.ss.load_page()
            return MenuAction(None, Action.NONE)
        if option == PREV_PAGE.key:
            self.ss.page -= 1
            self.ss.load_page()
            return MenuAction(None, Action.NONE)

        if option.isdigit():
            # validated in get input; no indexerror possible
            current_page = self.ss.load_page().results
            return MenuAction(
                MangaMenu(current_page[int(option) - 1], self.cfg), Action.PUSH
            )

        return self.handle_option_defaults(option)


class MangaMenu(Menu):
    """Where the user can perform actions on their chosen Manga."""

    description = "Chosen manga: "
    CG = MANGA_CONTROLS

    def __init__(self, chosen_manga: Manga, cfg: Config):
        self.manga = chosen_manga
        super().__init__(cfg)  # To init self.ansi
        title_display = self.ansi.to_underline(chosen_manga.title)
        self.description += title_display

    def show(self):
        self.utils.clear()
        super().show()

    def handle_option(self, option: str) -> MenuAction:
        if option == DOWNLOAD.key:
            return MenuAction(MangaFeedMenu(self.manga, self.cfg), Action.PUSH)
        if option == VIEW_INFO.key:
            print("WORK IN PROGRESS")
            return MenuAction(None, Action.NONE)

        return self.handle_option_defaults(option)


class MangaFeedMenu(Menu):
    """
    Displays chapters that the user can select for downloading.

    (This is displayed following `MangaMenu` or manga URL download).
    """

    USE_GETCH = False
    CG = PAGE_CONTROLS_CHAPTERS
    description = "Use 'Help' to view info on how to select chapters."

    selection_help = textwrap.dedent(  # TODO: style this with ANSI
        """\
        Ways to select chapters to download:
        
        - A chapter: "2"
        - Multiple chapters: "2, 5, 8"
        - A range of chapters: "3-8"
        - Multiple ranges of chapters: "3-8, 11-13, 15-17"
        
        Ranges of chapters also include the starting and ending number.
        e.g. "5-8" = Chapter 5, 6, 7, 8
        
        Make sure to use the indices (numbers) on the left, not the
        chapter numbers themselves!
        
        If you're new to terminals, you can press the up arrow (↑)
        to retrieve your last input.
        
        Press any key to continue...\
        """
    )

    def __init__(self, chosen_manga: Manga, cfg: Config):
        self.manga = chosen_manga
        super().__init__(cfg)  # to init self.ansi
        title_display = f"Chosen manga: {self.ansi.to_underline(chosen_manga.title)}\n"
        self.description = title_display + self.description
        self.cp = ChapterPaginator(chosen_manga, cfg)

    def show(self):
        self.utils.clear()
        print(self.description)
        self.utils.print_chapter_titles(self.cp.load_page())
        print(
            self.ansi.to_inverse(f"  Page {self.cp.page + 1}/{self.cp.total_pages}  ")
        )
        print()
        self._show_controls()

    def _error_in(self, error_msg: str):
        self.ansi.to_err(error_msg)

    def get_option(self) -> str:
        """Gets a validated option from the user."""
        while True:
            self.utils.clear()
            self.show()
            user_input = input(">> ").strip().upper()

            logger.debug(
                "User input '%s' from class: %s", user_input, type(self).__name__
            )

            if user_input in self.keys:
                return user_input
            print(self.ansi.to_err("\nInvalid input"))
            time.sleep(self.cfg.cli.time_to_read)

    def handle_option(self, option: str) -> MenuAction:
        if option == PREV_PAGE.key:
            self.cp.page -= 1
            return MenuAction(None, Action.NONE)
        if option == NEXT_PAGE.key:
            self.cp.page += 1
            return MenuAction(None, Action.NONE)
        if option == HELP.key:
            self.utils.clear()
            print(self.selection_help)
            self.utils.get_input_key()
            return MenuAction(None, Action.NONE)

        return self.handle_option_defaults(option)
