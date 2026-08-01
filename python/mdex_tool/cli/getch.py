# type: ignore
"""
Performs getch() with cross-platform compatibility.

From: https://github.com/joeyespo/py-getch/blob/master/getch/getch.py
"""

# pylint:disable= unused-import import-outside-toplevel

try:
    from msvcrt import getch
except ImportError:

    def getch():
        """
        Gets a single character from STDIO.
        """
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
