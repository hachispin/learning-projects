"""the entry point :)"""

import logging

from mdex_dl.cli.menus import MainMenu, MenuStack
from mdex_dl.load_config import require_ok_config
from mdex_dl.logger import setup_logging

cfg = require_ok_config()
setup_logging(cfg.logging)
logger = logging.getLogger(__name__)
logger.debug("Hello, world!")
logger.debug("Config: %r", cfg)
stack = MenuStack([MainMenu(cfg)])


def main():
    """The GUI loop."""
    while True:
        top = stack.peek()

        if top is not None:
            top.show()
            option = top.get_option()
            action = top.handle_option(option)
            stack.handle_action(action)
        else:
            break


if __name__ == "__main__":
    main()
