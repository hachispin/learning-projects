"""
Sets up `logging.basicConfig` with the function
`setup_logging()`for use in other modules.

Logging may also be disabled if configured as such.
"""

from pathlib import Path
import logging
from datetime import datetime

from mdex_dl import PROJECT_ROOT
from mdex_dl.models import LoggingConfig


def setup_logging(logging_cfg: LoggingConfig) -> None:
    """Sets up (or disables) logging according to rules set in config."""
    cfg = logging_cfg

    if not cfg.enabled:
        logging.disable(logging.CRITICAL)
    else:
        log_dir = Path(PROJECT_ROOT / cfg.location)
        log_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=f"{log_dir}/mdex_dl_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",  # noqa
            filemode="w",
            level=cfg.level,
            format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        )
