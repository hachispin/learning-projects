"""
Stores utilities used for the CLI such as printing
Manga tuples and validating inputs for specific menus
under the CliUtils class.
"""

import os
import sys
from typing import Callable

from mdex_tool.cli.ansi.output import AnsiOutput
from mdex_tool.cli.getch import getch  # type: ignore
from mdex_tool.models import Chapter, Config, Manga


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
        """
        Normalises input to be compared against uppercase Control.key values.

        Note that this uses getch(), flushing user input on first character.
        """
        print(">> ", flush=True, end="")
        option = getch()

        if isinstance(option, bytes):
            option = option.decode()

        option = option.upper()
        print(option)
        return option

    def parse_selection(  # pylint:disable=too-many-return-statements
        self, user_input: str, error_out: Callable[[str], None]
    ) -> list[int]:
        """
        Parses selections such as:

            - A chapter: "2"
            - Multiple chapters: "2, 5, 8"
            - Range of chapters: "3-8"
            - Multiple ranges of chapters: "3-8, 11-13, 15-17"

        into a list of integers.

        If the selection is invalid, an empty list is returned.

        Args:
            user_input (str): the selection

        Returns:
            list[int]: the numbers that the selection covers
        """
        user_input = user_input.strip(",")  # Remove trailing
        selections = tuple(s.strip() for s in user_input.split(","))
        nums = []  # type: list[int]

        if all(not s for s in selections):
            error_out("Selection can't be blank")
            return []

        allowed = set("0123456789-")
        if any(ch not in allowed for s in selections for ch in s):
            error_out(
                "Unexpected character; only numbers, dashes, commas and spaces are allowed"
            )
            return []

        for s in selections:
            # all chars in `s` must now be digits or dashes
            if not s:
                error_out("No selection found between comma (e.g. 2,,4)")
                return []

            if s.isdigit():
                nums.append(int(s))
                continue

            # must include one or more dashes if not digit
            if s.count("-") > 1:
                error_out(f"{repr(s)}: Range selections can only have one dash")
                return []

            start, _, stop = s.partition("-")
            if not start or not stop:
                error_out(
                    f"{repr(s)}: Both sides of a dash must have numbers to be a valid range"
                )
                return []

            if int(start) > int(stop):
                error_out(
                    f"{repr(s)}: A range selection's start must be below its end."
                )
                return []
            nums += range(int(start), int(stop) + 1)

        return sorted(list(set(nums)))

    def print_manga_titles(self, manga: tuple[Manga, ...]):
        """Prints manga titles with a left index for use by the user."""
        for idx, m in enumerate(manga):
            print(f"[{idx+1}]: {m.title}")

    def print_chapter_titles(self, chapters: tuple[Chapter, ...], page: int = 0):
        """Prints chapter titles with a left index for use by the user."""
        print()
        offset = page * self.cfg.search.results_per_page
        for idx, c in enumerate(chapters):
            if c.chap_num is None:
                print(f"[{offset+idx+1}]: {c.title}")
            else:
                print(f"[{offset+idx+1}]: Ch. {c.chap_num}")
        print()
