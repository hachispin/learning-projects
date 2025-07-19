from mdex_dl.utils import get_project_root
from mdex_dl.load_config import Config

from pathlib import Path
import logging
from datetime import datetime


def setup_logging(config: Config) -> None:
    cfg = config["logging"]

    if not cfg["enabled"]:
        logging.disable(logging.CRITICAL)
    else:
        log_dir = Path(get_project_root() / cfg["location"])
        logging.basicConfig(
            filename=f"{log_dir}/mdex_dl_{datetime.now():%Y-%m-%d_%H-%M-%S}.log",  # noqa
            filemode="w",
            level=cfg["level"],
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
