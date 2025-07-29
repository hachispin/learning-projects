"""
Where the AnsiOutput class is stored.
"""

from mdex_dl.models import CliConfig
from mdex_dl.cli.ansi.text_styles import BOLD, DIM, INVERSE, ITALIC, RESET, UNDERLINE
from mdex_dl.cli.ansi.fg_colors import CYAN, GREEN, RED, DEFAULT, YELLOW


class AnsiOutput:
    """Groups methods that use ANSI."""

    def __init__(self, cfg: CliConfig):
        self.use_ansi = cfg.use_ansi

    def format_ansi(
        self,
        message: str,
        text_styles: tuple[str, ...] = (RESET,),
        fg_color: str = DEFAULT,
    ):
        """
        Formats the message with the given ANSI enums.

        If ANSI is not enabled, return original message.
        """
        if not self.use_ansi:
            return message

        codes = f"{';'.join(text_styles)};{fg_color}"
        return f"\033[{codes}m{message}\033[0m"

    def print_ansi(
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
        print(self.format_ansi(message, text_styles, fg_color), end=end)

    def to_success(self, message: str) -> str:
        """Returns the message in a 'success' style; green"""
        return self.format_ansi(message, fg_color=GREEN)

    def to_err(self, message: str) -> str:
        """Returnes the message in an 'error' style; bold and red."""
        return self.format_ansi(message, text_styles=(BOLD,), fg_color=RED)

    def to_warn(self, message: str) -> str:
        """Returns the message in a 'warning' style; italics and yellow"""
        return self.format_ansi(message, text_styles=(ITALIC,), fg_color=YELLOW)

    def to_inverse(self, message: str) -> str:
        """Returns the message with inverted colours."""
        return self.format_ansi(message, text_styles=(INVERSE,))

    def to_dim(self, message: str) -> str:
        """Returns the message slightly greyed out."""
        return self.format_ansi(message, text_styles=(DIM,))

    def to_underline(self, message: str) -> str:
        """Returns the message underlined."""
        return self.format_ansi(message, text_styles=(UNDERLINE,))


class ProgressBar(AnsiOutput):
    """A class used to display a progress bar with display()"""

    _CARRIAGE_RETURN_PAD = " " * 4
    _HIDE_CURSOR = "\033[?25l"
    _SHOW_CURSOR = "\033[?25h"
    _REDBAR = "\033[31m━\033[0m"
    _GREENBAR = "\033[32m━\033[0m"

    def __init__(self, cfg: CliConfig, label: str = "Loading...", bars: int = 20):
        self.label = label
        self.bars = bars
        super().__init__(cfg)

    def _display_no_ansi(self, percentage: str):
        """Prints a progress bar without ANSI."""
        output = f"{self.label} {percentage}"
        print(output + self._CARRIAGE_RETURN_PAD, end="\r")

        if percentage == "100%":
            print()

    def _display_err_no_ansi(self):
        """Prints a progress bar's error form without ANSI."""
        print(f"{self.label} FAILED ERR%")

    def display(self, progress: float):
        """
        Prints a progress bar.

        If the argument `progress` is -1.0, the process (that's being
        displayed by the progress bar) is considered to have failed,
        so the display_err() method is called instead.

        Args:
            progress (float): from 1.0 to 0.0; how close something is to being complete
            label (str): the progress bar's label
            bars (int, optional): how many bars to display. Defaults to 20.

        Raises:
            ValueError: if `progress` is not within the range 0.0 <= x <= 1
                and not equal to -1.0
        """
        if progress == -1.0:
            self._display_err()
            return

        perc = f"{round(progress * 100)}%"
        if not self.use_ansi:
            self._display_no_ansi(perc)
            return

        print(ProgressBar._HIDE_CURSOR, end="")

        if progress > 1.0:
            raise ValueError("Progress cannot be greater than 100% (1.0)")
        if progress < 0.0:
            raise ValueError("Progress cannot be less than 0% (0.0) if it's not -1.0")

        complete_bars = int(self.bars * progress)
        progress_bar = ProgressBar._GREENBAR * complete_bars
        progress_bar += ProgressBar._REDBAR * (self.bars - complete_bars)

        self.print_ansi(self.label, fg_color=CYAN, end=" ")
        print(f"{progress_bar}", end=" ")
        self.print_ansi(perc + self._CARRIAGE_RETURN_PAD, fg_color=RED, end="\r")

        if progress == 1.0:
            print()

        print(ProgressBar._SHOW_CURSOR, end="")
        return

    def _display_err(self):
        """Prints a progress bar's error form"""

        if not self.use_ansi:
            self._display_err_no_ansi()
            return

        self.print_ansi(self.label, fg_color=CYAN, end=" ")
        self.print_ansi("FAILED", text_styles=(INVERSE,), fg_color=RED, end=" ")
        # Shorten bars to keep line-width consistent if possible
        bars = self.bars - 7  # 7 = len(" FAILED")
        if self.bars - 7 <= 0:
            bars = 0

        print(ProgressBar._REDBAR * bars, end=" ")
        self.print_ansi("ERR%", fg_color=RED)
