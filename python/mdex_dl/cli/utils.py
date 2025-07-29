"""
Stores utilities used for the CLI such as printing
Manga tuples and validating inputs for specific menus
under the CliUtils class.
"""

import os
import sys
import time

from mdex_dl.cli.ansi.output import AnsiOutput
from mdex_dl.cli.controls.classes import ControlGroup
from mdex_dl.cli.controls.constants import PAGE_CONTROLS, QUIT
from mdex_dl.cli.getch import getch  # type: ignore
from mdex_dl.models import Chapter, Config, Manga, SearchResults


class CliUtils:
    """Contains general CLI utilities."""

    if sys.platform == "win32":

        def clear(self):
            """Clears the terminal."""
            os.system("cls")

    else:

        def clear(self):
            """Clears the terminal."""
            os.system("clear")

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.ansi = AnsiOutput(cfg.cli)

    def get_input_key(self) -> str:
        """Normalises input to be compared against uppercase Control.key values."""
        print(">> ", flush=True, end="")
        option = getch()

        if isinstance(option, bytes):
            option = option.decode()

        option = option.upper()
        print(option)
        return option

    def get_option(self, cg: ControlGroup, message: str | None = None) -> str:
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
            self.clear()
            if message:
                print(message + "\n")
            self.print_controls(cg)
            user_input = self.get_input_key()

            if user_input == QUIT.key:
                sys.exit(0)
            if user_input in allowed:
                return user_input

            print(self.ansi.to_err("[Invalid option]"))
            time.sleep(self.cfg.cli.time_to_read)

        # getch() isn't used here since manga indices can be two characters (e.g. "10")

    def get_page_option(
        self,
        res: SearchResults,
        current_page: int,
        total_pages: int,
        last_index: int | None = None,
    ) -> str:
        """
        Gets a valid page option or manga index from the user for the page menu.

        This also prints the
        necessary information needed for the user to choose their option.

        Args:
            last_index (int, optional): the last index that the user can pick.
                **This should be one-indexed** as the index is user-facing.

                Defaults to cfg.search.results_per_page, which should be the
                last index given a full page.

        Returns:
            str: the validated option the user picked; may be a manga index or
                a page control.
        """
        if last_index is None:
            last_index = self.cfg.search.results_per_page

        allowed = [c.key for c in PAGE_CONTROLS.controls]
        allowed += list(str(i) for i in range(1, last_index + 1))
        total_pages = (res.total // self.cfg.search.results_per_page) + 1

        while True:
            self.clear()

            self.print_manga_titles(res.results)
            print(self.ansi.to_inverse(f"Page {current_page+1} / {total_pages}\n"))
            print("Type the manga's number on the left to select, or:")
            self.print_controls(PAGE_CONTROLS)

            user_input = input(">> ").upper()
            if user_input == QUIT.key:
                sys.exit(0)
            if user_input in allowed:
                return user_input
            # failure cases
            if user_input.isdigit():
                print(self.ansi.to_err("[Invalid manga index]"))
            else:
                print(self.ansi.to_err("[Invalid page control]"))

            time.sleep(self.cfg.cli.time_to_read)

    def print_manga_titles(self, manga: tuple[Manga, ...]):
        """Prints manga titles with a left index for use by the user."""
        for idx, m in enumerate(manga):
            print(f"[{idx+1}]: {m.title}")

    def print_chapter_titles(self, chapters: tuple[Chapter, ...]):
        """Prints chapter titles with a left index for use by the user."""
        for idx, c in enumerate(chapters):
            print(f"[{idx+1}]: {c.title}")
