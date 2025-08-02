"""
Contains all the classes that are used in other modules.

These classes are only meant as containers; they shouldn't
have logic.
"""

from dataclasses import dataclass


@dataclass
class Manga:
    """
    Args:
        title (str, required): the manga title as given by the API
        uuid (str, required): UUID used for GET requests
    """

    title: str
    uuid: str
    # TODO: add tags


@dataclass
class Chapter:
    """
    Args:
        uuid (str): UUID used for GET requests
        chap_num (str | None): used to name dirs upon download
    """

    uuid: str
    chap_num: str | None = None

    def __post_init__(self):
        self.title = f"Ch. {self.chap_num or 'Unknown'}"


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

    - `filenames_data` means normal quality images.
    - `filenames_data_saver` means compressed images.

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#howto
    """

    base_url: str
    chapter_hash: str
    filenames_data: tuple[str, ...]
    filenames_data_saver: tuple[str, ...]


@dataclass
class MangaResults:
    """Contains info gathered when `GET /manga` is invoked."""

    results: tuple[Manga, ...]
    total: int


@dataclass
class ReqsConfig:
    """Stores settings for [reqs] in config.toml"""

    api_root: str
    report_endpoint: str
    get_timeout: int | float
    post_timeout: int | float


@dataclass
class RetryConfig:
    """Stores settings for [retry] in config.toml"""

    max_retries: int
    backoff_factor: int | float
    backoff_jitter: int | float
    backoff_max: int | float


@dataclass
class SaveConfig:
    """Stores settings for [save] in config.toml"""

    location: str
    max_title_length: int


@dataclass
class ImagesConfig:
    """Stores settings for [images] in config.toml"""

    use_datasaver: bool


@dataclass
class SearchConfig:
    """Stores settings for [search] in config.toml"""

    results_per_page: int
    include_pornographic: bool


@dataclass
class CliConfig:
    """Stores settings for [cli] in config.toml"""

    options_per_row: int
    use_ansi: bool
    time_to_read: int | float


@dataclass
class LoggingConfig:
    """Stores settings for [logging] in config.toml"""

    enabled: bool
    level: str | int  # converted from string literal (e.g. "CRITICAL")
    location: str  # to int with _nameToLevel()


@dataclass
class Config:
    """Full config for config.toml"""

    reqs: ReqsConfig
    save: SaveConfig
    retry: RetryConfig
    images: ImagesConfig
    search: SearchConfig
    cli: CliConfig
    logging: LoggingConfig
