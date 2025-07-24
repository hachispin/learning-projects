"""Stores named ControlGroup constants used in the CLI."""

from mdex_dl.cli.controls.classes import Control, ControlGroup

# fmt: off
# ^ for consistent arg ordering

BACK = Control("[Z] Back", "Z")
EXIT = Control("[X] Exit", "X")

MAIN_MENU_CONTROLS = ControlGroup(
    (
        Control("[S]earch", "S"),
        Control("[D]ownload", "D"),
        EXIT,
    )
)
PAGE_CONTROLS = ControlGroup(
    (
        Control("[Q] Previous", "Q"),
        Control("[E] Next", "E"),
        BACK,
        EXIT
    )
)
MANGA_CONTROLS = ControlGroup(
    (
        Control("[D]ownload", "D"),
        Control("[V]iew info", "V"),
        BACK,
        EXIT,
    )
)
