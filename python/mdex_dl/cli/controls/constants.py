"""Stores named ControlGroup constants used in the CLI."""

from mdex_dl.cli.controls.classes import Control, ControlGroup


BACK = Control("[B] Back", "B")
QUIT = Control("[Q] Quit", "Q")
SEARCH = Control("[S] Search", "S")
DOWNLOAD = Control("[D] Download", "D")
NEXT_PAGE = Control("[N] Next", "N")
LAST_PAGE = Control("[L] Last", "L")
VIEW_INFO = Control("[V] View info", "V")

MAIN_MENU_CONTROLS = ControlGroup(
    (
        SEARCH,
        DOWNLOAD,
        QUIT,
    )
)

PAGE_CONTROLS = ControlGroup(
    (
        LAST_PAGE,
        NEXT_PAGE,
        BACK,
        QUIT,
    )
)

MANGA_CONTROLS = ControlGroup(
    (
        DOWNLOAD,
        VIEW_INFO,
        BACK,
        QUIT,
    )
)
