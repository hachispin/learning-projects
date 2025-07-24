"""
Where the print_ansi() function is stored.
"""

from mdex_dl.models import CliConfig
from mdex_dl.cli.ansi.text_styles import BOLD, ITALIC, RESET
from mdex_dl.cli.ansi.fg_colors import RED, DEFAULT, YELLOW


class AnsiOutput:
    """Groups methods that use ANSI."""

    def __init__(self, cfg: CliConfig):
        self.use_ansi = cfg.use_ansi

    def _print_ansi(
        self,
        message: str,
        *,  # enforce kwargs because we're using ansi namespace
        text_styles: tuple[str, ...] = (RESET,),
        fg_color: str = DEFAULT,
    ):
        """
        Prints the message's ANSI representation using all the
        given ANSI enums for text style(s) and foreground colour(s).

        If ANSI is disabled in the config, default to the normal print()

        Example usage:
            `self.print_ansi(message, text_styles=(BOLD,), fg_color=RED)`

        Args:
            message (str): the message to be stylised
        """
        if not self.use_ansi:
            print(message)
        else:  # unpack
            codes = f"{';'.join(text_styles)};{fg_color}"
            print(f"\033[{codes}m{message}\033[0m")

    def print_err(self, message: str):
        """Prints in an 'error' style; bold and red."""
        self._print_ansi(message, text_styles=(BOLD,), fg_color=RED)

    def print_warn(self, message: str):
        """Prints in a 'warning' style; italics and yellow"""
        self._print_ansi(message, text_styles=(ITALIC,), fg_color=YELLOW)


if __name__ == "__main__":
    fake_cfg = CliConfig(options_per_row=3, use_ansi=True)
    a = AnsiOutput(fake_cfg)
    a.print_err("bro it's cooked")
    a.print_warn("just kidding, it's not that bad")
