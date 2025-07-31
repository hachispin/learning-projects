"""
Stores utilities used for the CLI such as printing
Manga tuples and validating inputs for specific menus
under the CliUtils class.
"""

import os
import sys
from typing import Callable

from mdex_dl.cli.ansi.output import AnsiOutput
from mdex_dl.cli.getch import getch  # type: ignore
from mdex_dl.models import Chapter, Config, Manga


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

    def parse_chapter_selection(
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
        user_input = user_input.replace(" ", "")
        if not user_input:
            error_out("Selection cannot be blank")
            return []
        if user_input[-1] == ",":  # Remove trailing comma
            user_input = user_input[:-1]

        # Regex for the homeless
        if not all(ch.isdigit() or ch in {"-", ","} for ch in user_input):
            error_out(
                "Selection must only consist of spaces, dashes, commas and numbers"
            )
            return []

        selections = user_input.split(",")
        ranges = []  # type: list[str]
        nums = []  # type: list[int]

        for s in selections:
            if s.isdigit():
                nums.append(int(s))
            else:
                ranges.append(s)

        for r in ranges:
            if r.count("-") != 1:

                error_out("Invalid range syntax: must be in the format {start}-{stop}")
                return []
            start, stop = r.split("-")
            assert start.isdigit() and stop.isdigit()
            if int(start) > int(stop):
                error_out(
                    "Invalid range: starting number cannot be greater than the ending number"
                )
                return []
            nums += list(range(int(start), int(stop) + 1))

        return list(set(nums))

    def print_manga_titles(self, manga: tuple[Manga, ...]):
        """Prints manga titles with a left index for use by the user."""
        for idx, m in enumerate(manga):
            print(f"[{idx+1}]: {m.title}")

    def print_chapter_titles(self, chapters: tuple[Chapter, ...]):
        """Prints chapter titles with a left index for use by the user."""
        for idx, c in enumerate(chapters):
            print(f"[{idx+1}]: {c.title}")
