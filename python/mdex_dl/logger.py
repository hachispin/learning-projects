"""
Sets up `logging.basicConfig` with the function
`setup_logging()`for use in other modules.

Logging may also be disabled if configured as such.
"""

from pathlib import Path
import logging
from datetime import datetime

from mdex_dl.load_config import Config


project_root = Path(__file__).parent


def setup_logging(config: Config) -> None:
    """Sets up (or disables) logging according to rules set in config."""
    cfg = config["logging"]

    if not cfg["enabled"]:
        logging.disable(logging.CRITICAL)
    else:
        log_dir = Path(project_root / cfg["location"])
        logging.basicConfig(
            filename=f"{log_dir}/mdex_dl_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",  # noqa
            filemode="w",
            level=cfg["level"],
            format="%(asctime)s [%(levelname)s] %(message)s",
        )
