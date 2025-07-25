"""
Where the AnsiOutput class is stored.
"""

from mdex_dl.models import CliConfig
from mdex_dl.cli.ansi.text_styles import BOLD, INVERSE, ITALIC, RESET
from mdex_dl.cli.ansi.fg_colors import CYAN, RED, DEFAULT, YELLOW


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
        end: str = "\n",
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
            print(f"\033[{codes}m{message}\033[0m", end=end)

    def print_err(self, message: str):
        """Prints in an 'error' style; bold and red."""
        self._print_ansi(message, text_styles=(BOLD,), fg_color=RED)

    def print_warn(self, message: str):
        """Prints in a 'warning' style; italics and yellow"""
        self._print_ansi(message, text_styles=(ITALIC,), fg_color=YELLOW)

    def print_invert(self, message: str):
        """Prints the message with inverted colours."""
        self._print_ansi(message, text_styles=(INVERSE,))


class ProgressBar(AnsiOutput):
    """A class used to display a progress bar with display()"""

    _HIDE_CURSOR = "\033[?25l"
    _SHOW_CURSOR = "\033[?25h"
    _REDBAR = "\033[31m━\033[0m"
    _GREENBAR = "\033[32m━\033[0m"

    def __init__(self, cfg: CliConfig, label: str = "Loading...", bars: int = 20):
        self.label = label
        self.bars = bars
        super().__init__(cfg)

    def _display_no_ansi(self, percentage: str):
        output = f"{self.label} {percentage}"
        print(output, end="\r")

        if percentage == "100%":
            print()

    def display(self, progress: float):
        """
        Prints a progress bar.

        Args:
            progress (float): from 1.0 to 0.0; how close something is to being complete
            label (str): the progress bar's label
            bars (int, optional): how many bars to display. Defaults to 20.

        Raises:
            ValueError: if `progress` is not within the range 0.0 <= x <= 1
        """
        perc = f"{round(progress * 100)}%"
        if not self.use_ansi:
            self._display_no_ansi(perc)
            return

        print(ProgressBar._HIDE_CURSOR, end="")

        if progress > 1.0:
            raise ValueError("Progress cannot be greater than 100% (1.0)")
        if progress < 0.0:
            raise ValueError("Progress cannot be less than 0% (0.0)")

        complete_bars = int(self.bars * progress)
        progress_bar = ProgressBar._GREENBAR * complete_bars
        progress_bar += ProgressBar._REDBAR * (self.bars - complete_bars)

        self._print_ansi(self.label, fg_color=CYAN, end=" ")
        print(f"{progress_bar}", end=" ")
        self._print_ansi(perc, fg_color=RED, end="\r")

        if progress == 1.0:
            print()

        print(ProgressBar._SHOW_CURSOR, end="")
        return

    def display_err(self):
        """Prints a progress bar's error form"""
        self._print_ansi(self.label, fg_color=CYAN, end=" ")
        self._print_ansi("FAILED", text_styles=(INVERSE,), fg_color=RED, end=" ")
        # Shorten bars to keep line-width consistent
        bars = self.bars - 7  # 7 = len(" FAILED")
        if self.bars - 7 <= 0:
            bars = self.bars

        print(ProgressBar._REDBAR * bars, end=" ")
        self._print_ansi("ERR%", fg_color=RED)
