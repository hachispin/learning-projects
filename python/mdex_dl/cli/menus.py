"""Stores classes used to handle menus"""

from mdex_dl.cli.controls.classes import ControlGroup
from mdex_dl.models import Config


class Menu:
    """shut up pylint"""

    def __init__(
        self,
        cg: ControlGroup,
        cfg: Config,
        description: str | None = None,
    ):
        self.cg = cg
        self.cfg = cfg
        self.description = description


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
