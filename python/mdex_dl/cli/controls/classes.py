from dataclasses import dataclass

from mdex_dl.cli.ansi.output import AnsiOutput


@dataclass
class Control:
    """
    Contains a control and its description used for UI navigation.

    Raises:
        ValueError: if the key isn't length one
    """

    label: str  # e.g. "[D]ownload" or "[Q] Next page"
    key: str  #   e.g. "D", "Q"

    def __post_init__(self):
        if not self.label or not self.key:
            raise ValueError("Control.key and Control.label must not be empty")
        if len(self.key) != 1:
            raise ValueError("Control.key must be length one")

    def render(self):
        # Find the key in self.label to underline
        ...


@dataclass
class ControlGroup:
    """
    Contains a tuple of Control dataclasses.
    """

    controls: tuple[Control, ...]
