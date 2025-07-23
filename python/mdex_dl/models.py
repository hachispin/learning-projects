"""
Contains all classes and subclassed exceptions
that are used in other modules.

Note that no functionality is here; common
functions instead are in `mdex_dl.utils`
"""

from dataclasses import dataclass


class Manga:
    """
    Parameters:
        title (str, required): the manga title as given by the API
        id (str, required): UUID used for GET requests
        tags (list[str], optional): list of genres used for searching
    """

    def __init__(self, title: str, uuid: str):  # TODO: add tags
        self.title = title
        self.uuid = uuid

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):
        return f"Manga({repr(self.title)}, {repr(self.uuid)}"


class Chapter:
    """
    Parameters:
        id (str): UUID used for GET requests
        chap_num (str | None): used to name dirs upon download
    """

    def __init__(self, uuid: str, chap_num: str | None):
        self.title = f"Ch. {chap_num or "Unknown"}"
        self.uuid = uuid
        self.chap_num = chap_num

    def __repr__(self) -> str:
        return f"{repr(self.uuid), repr(self.chap_num)}"

    def __str__(self):
        return self.title


@dataclass
class ImageReport:
    """
    Contains telemetry structure gathered during download which
    is sent to the MangaDex@Home report endpoint.

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#the-mangadexhome-report-endpoint
    """

    url: str
    success: bool
    cached: bool
    size_bytes: int
    duration_ms: int


@dataclass
class ChapterGetResponse:
    """
    Contains the expected response data from the
    `GET /at-home/server/:chapterId` endpoint.

    - filenames_data means normal quality images.
    - filenames_data_saver means compressed images.

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#howto
    """

    base_url: str
    chapter_hash: str
    filenames_data: tuple[str, ...]
    filenames_data_saver: tuple[str, ...]


@dataclass
class SearchResults:
    """Contains info gathered when `GET /manga` is invoked"""

    results: tuple[Manga, ...]
    total: int


@dataclass
class ReqsConfig:
    """Type hints for [reqs] in config.toml"""

    api_root: str
    report_endpoint: str
    get_timeout: int | float
    post_timeout: int | float


@dataclass
class RetryConfig:
    """Type hints for [retry] in config.toml"""

    max_retries: int
    backoff_factor: int | float
    backoff_jitter: int | float
    backoff_max: int | float


@dataclass
class SaveConfig:
    """Type hints for [save] in config.toml"""

    location: str
    max_title_length: int


@dataclass
class ImagesConfig:
    """Type hints for [images] in config.toml"""

    use_datasaver: bool


@dataclass
class SearchConfig:
    """Type hints for [search] in config.toml"""

    results_per_page: int
    include_pornographic: bool


@dataclass
class CliConfig:
    """Type hints for [cli] in config.toml"""

    options_per_row: int
    use_ansi: bool


@dataclass
class LoggingConfig:
    """Type hints for [logging] in config.toml"""

    enabled: bool
    level: str | int  # converted from string literal (e.g. "CRITICAL")
    location: str  # to int with _nameToLevel()


@dataclass
class Config:
    """Full type hints for config.toml"""

    reqs: ReqsConfig
    save: SaveConfig
    retry: RetryConfig
    images: ImagesConfig
    search: SearchConfig
    cli: CliConfig
    logging: LoggingConfig
