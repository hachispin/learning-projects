# pylint: disable=missing-module-docstring
import tomllib
from pathlib import Path
from logging import _nameToLevel  # Private but it's fine I think
from typing import TypedDict

# pylint: enable=missing-module-docstring
from mdex_dl.models import ConfigError
from mdex_dl.utils import get_project_root


# These are all just for static type checkers
class ReqsConfig(TypedDict):
    """Type hints for [reqs] in config.toml"""

    api_root: str
    report_endpoint: str
    max_retries: int
    base_delay: int | float
    base_delay_ratelimit: int | float
    get_timeout: int | float
    post_timeout: int | float


class SaveConfig(TypedDict):
    """Type hints for [save] in config.toml"""

    location: str
    max_title_length: int


class ImagesConfig(TypedDict):
    """Type hints for [images] in config.toml"""

    use_datasaver: bool


class SearchConfig(TypedDict):
    """Type hints for [search] in config.toml"""

    results_per_page: int
    include_pornographic: bool


class CliConfig(TypedDict):
    """Type hints for [cli] in config.toml"""

    options_per_row: int
    use_ansi: bool


class LoggingConfig(TypedDict):
    """Type hints for [logging] in config.toml"""

    enabled: bool
    level: str | int  # converted from string literal (e.g. "CRITICAL")
    location: str  # to int with _nameToLevel()


class Config(TypedDict):
    """Full type hints for config.toml"""

    reqs: ReqsConfig
    save: SaveConfig
    images: ImagesConfig
    search: SearchConfig
    cli: CliConfig
    logging: LoggingConfig


project_root = get_project_root()


# pylint: disable=missing-function-docstring
def is_bool(x):
    return isinstance(x, bool)


def is_int(x):
    return isinstance(x, int)


def is_str(x):
    return isinstance(x, str)


def is_numeric(x):
    return isinstance(x, float) or isinstance(x, int)


def get_dirname_problems(option_name: str, dirname: str) -> str | None:
    for char in dirname:
        if not (char.isalnum() or char in ("_", "-") or char == " " and dirname):
            return f"{option_name}: invalid dirname"
    return None


# pylint: enable=missing-function-docstring
def require_ok_config() -> Config:  # or throws ConfigError
    """
    Just check magic constraints on each config option because
    I'm lazy. Raises ConfigError if invalid, else return config
    """
    cfg_fp = Path(get_project_root() / "config.toml")
    print(cfg_fp)

    try:
        with cfg_fp.open("rb") as f:
            cfg: Config = tomllib.load(f)  # type: ignore
    except FileNotFoundError:
        raise ConfigError(
            errors=["Config file not found; expected config.toml in mdex_dl)"]
        ) from None

    bad_options = []

    # theres a lot of repetition here but I've
    # chosen not try to apply DRY because:
    #   - invalid options need to be known, many of     <- this also applies to
    #       the ways of 'shortening' remove this info       pydantic i think
    #   - the structure lines up with the config file
    #       (atleast if you don't lobotomise it)
    #   - there aren't many options so benefits are minimal

    reqs = cfg["reqs"]  # ReqsConfig

    if not reqs["api_root"].startswith("https://"):
        bad_options.append("api_root: invalid URL; must start with https://")

    if not reqs["report_endpoint"].startswith("https://"):
        bad_options.append("report_endpoint: invalid URL; must start with https://")

    if not is_int(reqs["max_retries"]):
        bad_options.append("images.max_retries: must be integer")
    elif reqs["max_retries"] < 0:
        bad_options.append("images.max_retries: must not be negative")

    if not is_numeric(reqs["base_delay"]):
        bad_options.append("reqs.base_delay must be int or float")
    elif reqs["base_delay"] < 0:
        bad_options.append("reqs.base_delay: must not be negative")

    if not is_numeric(reqs["base_delay_ratelimit"]):
        bad_options.append("reqs.base_delay must be int or float")
    elif reqs["base_delay_ratelimit"] < 0:
        bad_options.append("reqs.base_delay: must not be negative")

    if not is_numeric(reqs["get_timeout"]):
        bad_options.append("reqs.get_timeout: must be int or float")
    elif reqs["get_timeout"] <= 0:
        bad_options.append("reqs.get_timeout: must be greater than zero")

    if not is_numeric(reqs["post_timeout"]):
        bad_options.append("reqs.post_timeout: must be int or float")
    elif reqs["post_timeout"] <= 0:
        bad_options.append("reqs.post_timeout: must be greater than zero")

    save = cfg["save"]  # SaveConfig

    if p := get_dirname_problems("save.location", save["location"]):
        bad_options.append(p)

    if not is_int(save["max_title_length"]):
        bad_options.append("save.max_title_length: must be integer")
    elif save["max_title_length"] > 255:
        bad_options.append("save.max_title_length: must not be greater than 255")
    elif save["max_title_length"] <= 0:
        bad_options.append("save.max_title_length: must be greater than zero")

    images = cfg["images"]  # ImagesConfig

    if not is_bool(images["use_datasaver"]):
        bad_options.append("images.use_datasaver: must be true or false")

    search = cfg["search"]  # SearchConfig

    if not is_int(search["results_per_page"]):
        bad_options.append("search.results_per_page: must be integer")
    elif search["results_per_page"] <= 0:
        bad_options.append("search.results_per_page: must be greater than zero")

    if not is_bool(search["include_pornographic"]):
        bad_options.append("search.include_pornographic: must be true or false")

    cli = cfg["cli"]  # CliConfig

    if not is_int(cli["options_per_row"]):
        bad_options.append("cli.options_per_row: must be integer")
    if cli["options_per_row"] <= 0:
        bad_options.append("cli.options_per_row: must be greater than zero")

    if not is_bool(cli["use_ansi"]):
        bad_options.append("cli.use_ansi: must be true or false")

    logging = cfg["logging"]  # LoggingConfig

    if not is_bool(logging["enabled"]):
        bad_options.append("logging.enabled: must be true or false")

    if not is_str(logging["level"]):
        bad_options.append("logging.level: must be string")

    elif logging["level"] not in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        bad_options.append(
            "logging.level: invalid option, must be: "
            "'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'"
        )
    else:  # Convert to internal numerical representation
        logging["level"] = _nameToLevel.get(logging["level"])  # type: ignore

    if p := get_dirname_problems("logging.location", logging["location"]):
        bad_options.append(p)

    if bad_options:
        raise ConfigError(errors=bad_options)
    return cfg


if __name__ == "__main__":
    z = require_ok_config()
    print(z)
