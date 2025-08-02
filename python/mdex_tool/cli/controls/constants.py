"""Stores named ControlGroup constants used in the CLI."""

from mdex_tool.cli.controls.classes import Control, ControlGroup


BACK = Control("[B] Back", "B")
QUIT = Control("[Q] Quit", "Q")
SEARCH = Control("[S] Search", "S")
DOWNLOAD = Control("[D] Download", "D")
NEXT_PAGE = Control("[N] Next", "N")
PREV_PAGE = Control("[P] Prev", "P")
VIEW_INFO = Control("[V] View info", "V")
HELP = Control("[H] Help", "H")  # for viewing help on how to select chapters

# fmt: off
MAIN_MENU_CONTROLS = ControlGroup((
    SEARCH,
    DOWNLOAD,
    QUIT,
))

PAGE_CONTROLS = ControlGroup((
    PREV_PAGE,
    NEXT_PAGE,
    BACK,
    QUIT,
))

PAGE_CONTROLS_CHAPTERS = ControlGroup((
    PREV_PAGE,
    NEXT_PAGE,
    HELP,
    BACK,
    QUIT,
))

MANGA_CONTROLS = ControlGroup((
    DOWNLOAD,
    VIEW_INFO,
    BACK,
    QUIT,
))
