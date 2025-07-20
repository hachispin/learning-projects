"""
Loads `config.toml` (in project root) and accumulates errors to be
raised with `ConfigError` if found, along with proper reasons.

This also contains the fully type-hinted config as **Config**, which
consists of its parts: **ReqsConfig**, **SaveConfig**, etc.
"""

import tomllib
from pathlib import Path
from logging import _nameToLevel  # Private but it's fine I think
from typing import TypedDict

from mdex_dl.errors import ConfigError


# These are all just for static type checkers
class ReqsConfig(TypedDict):
    """Type hints for [reqs] in config.toml"""

    api_root: str
    report_endpoint: str
    get_timeout: int | float
    post_timeout: int | float


class RetryConfig(TypedDict):
    """Type hints for [retry] in config.toml"""

    max_retries: int
    backoff_factor: int | float
    backoff_jitter: int | float
    backoff_max: int | float


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
    retry: RetryConfig
    images: ImagesConfig
    search: SearchConfig
    cli: CliConfig
    logging: LoggingConfig


project_root = Path(__file__).resolve().parent


# pylint: disable=missing-function-docstring
def is_bool(x):
    return isinstance(x, bool)


def is_int(x):
    return isinstance(x, int)


def is_str(x):
    return isinstance(x, str)


def is_numeric(x):
    return isinstance(x, (float, int))


def get_dirname_problems(option_name: str, dirname: str) -> str | None:
    for char in dirname:
        if not (char.isalnum() or char in ("_", "-") or char == " " and dirname):
            return f"{option_name}: invalid dirname"
    return None


# pylint: enable=missing-function-docstring
# pylint: disable=too-many-branches too-many-statements
def require_ok_config() -> Config:
    """
    Checks constraints and types of all values in `./config.toml`
    from the project root.

    Returns:
        Config (TypedDict): The fully typed config object.

    Raises:
        ConfigError: If any config values are of the wrong type or
        fail constraints
    """
    cfg_fp = Path(project_root / "config.toml")
    print(cfg_fp)

    try:
        with cfg_fp.open("rb") as f:
            cfg: Config = tomllib.load(f)  # type: ignore
    except FileNotFoundError:
        raise ConfigError(
            errors=["Config file not found; expected config.toml in mdex_dl)"]
        ) from None

    errors = []  # list[str]

    # theres a lot of repetition here but I've
    # chosen not try to apply DRY because:
    #   - invalid options need to be known, many of     <- this also applies to
    #       the ways of 'shortening' remove this info       pydantic i think
    #   - the structure lines up with the config file
    #       (atleast if you don't lobotomise it)
    #   - there aren't many options so benefits are minimal

    reqs = cfg["reqs"]  # ReqsConfig

    if not is_str(reqs["api_root"]):
        errors.append("reqs.api_root: must be a string")
    if not reqs["api_root"].startswith("https://"):
        errors.append("api_root: invalid URL; must start with https://")

    if not is_str(reqs["report_endpoint"]):
        errors.append("reqs.report_endpoint: must be a string")
    if not reqs["report_endpoint"].startswith("https://"):
        errors.append("report_endpoint: invalid URL; must start with https://")

    if not is_numeric(reqs["get_timeout"]):
        errors.append("reqs.get_timeout: must be int or float")
    elif reqs["get_timeout"] <= 0:
        errors.append("reqs.get_timeout: must be greater than zero")

    if not is_numeric(reqs["post_timeout"]):
        errors.append("reqs.post_timeout: must be int or float")
    elif reqs["post_timeout"] <= 0:
        errors.append("reqs.post_timeout: must be greater than zero")

    retry = cfg["retry"]  # RetryConfig

    if not is_int(retry["max_retries"]):
        errors.append("retry.max_retries: must be int")
    elif retry["max_retries"] < 0:
        errors.append("retry.max_retries: cannot be negative")

    if not is_numeric(retry["backoff_factor"]):
        errors.append("retry.backoff_factor: must be int or float")
    elif retry["backoff_factor"] < 0:
        errors.append("retry.backoff_factor: cannot be negative")

    if not is_numeric(retry["backoff_jitter"]):
        errors.append("retry.backoff_jitter: must be int or float")
    elif retry["backoff_jitter"] < 0:
        errors.append("retry.backoff_jitter: cannot be negative")

    if not is_numeric(retry["backoff_max"]):
        errors.append("retry.backoff_max: must be int or float")
    elif retry["backoff_max"] <= 0:
        errors.append("retry.backoff_max: must be greater than zero")

    save = cfg["save"]  # SaveConfig

    if p := get_dirname_problems("save.location", save["location"]):
        errors.append(p)

    if not is_int(save["max_title_length"]):
        errors.append("save.max_title_length: must be integer")
    elif save["max_title_length"] > 255:
        errors.append("save.max_title_length: must not be greater than 255")
    elif save["max_title_length"] <= 0:
        errors.append("save.max_title_length: must be greater than zero")

    images = cfg["images"]  # ImagesConfig

    if not is_bool(images["use_datasaver"]):
        errors.append("images.use_datasaver: must be true or false")

    search = cfg["search"]  # SearchConfig

    if not is_int(search["results_per_page"]):
        errors.append("search.results_per_page: must be integer")
    elif search["results_per_page"] <= 0:
        errors.append("search.results_per_page: must be greater than zero")

    if not is_bool(search["include_pornographic"]):
        errors.append("search.include_pornographic: must be true or false")

    cli = cfg["cli"]  # CliConfig

    if not is_int(cli["options_per_row"]):
        errors.append("cli.options_per_row: must be integer")
    if cli["options_per_row"] <= 0:
        errors.append("cli.options_per_row: must be greater than zero")

    if not is_bool(cli["use_ansi"]):
        errors.append("cli.use_ansi: must be true or false")

    logging = cfg["logging"]  # LoggingConfig

    if not is_bool(logging["enabled"]):
        errors.append("logging.enabled: must be true or false")

    if not is_str(logging["level"]):
        errors.append("logging.level: must be string")

    elif logging["level"] not in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        errors.append(
            "logging.level: invalid option, must be: "
            "'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'"
        )
    else:  # Convert to internal numerical representation
        logging["level"] = _nameToLevel.get(logging["level"])  # type: ignore

    if p := get_dirname_problems("logging.location", logging["location"]):
        errors.append(p)

    if errors:
        raise ConfigError(errors=errors)
    return cfg


if __name__ == "__main__":
    z = require_ok_config()
    print(z)
