"""
NOTE: Downloader class instances are created for
each chapter, and not for the entire manga
"""

# pylint:disable=unused-import c-extension-no-member
from http import client
import logging
from io import BytesIO
from os import makedirs
from pathlib import Path
import time
from typing import Self

import requests
import pycurl
import certifi

from mdex_dl.errors import ApiError
from mdex_dl.models import Chapter, Manga
from mdex_dl.api.http_config import get_retry_adapter
from mdex_dl.api.client import (
    get_with_ratelimit,
    get_cattributes,
    safe_to_json,
    assert_ok_response,
)
from mdex_dl.load_config import (
    Config,
    ReqsConfig,
    ImagesConfig,
    SaveConfig,
    RetryConfig,
)

logger = logging.getLogger(__name__)


class Downloader:
    """
    A class that wraps fetching, downloading and saving functionality
    for a specified `Chapter` object
    """

    def __init__(self, manga: Manga, chapter: Chapter, cfg: Config):
        logger.debug("Created Downloader() instance with chapter id: %s", chapter.id)

        # Create session binded to Retry() logic
        self.session = requests.session()
        adapter = get_retry_adapter(cfg["retry"])
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        # fmt: off
        self.reqs_cfg   = cfg["reqs"]       # ReqsConfig
        self.img_cfg    = cfg["images"]     # ImagesConfig
        self.save_cfg   = cfg["save"]       # SaveConfig
        self.retry_cfg  = cfg["retry"]      # RetryConfig - used for backoff
        # fmt: on                           logic with custom MangaDex headers
        self.chapter = chapter
        self.manga_title = manga.title

    def _get_with_ratelimit(self, url: str):
        """Packages get_with_ratelimit() from .api.client into a method"""
        return get_with_ratelimit(url, self.session, self.retry_cfg, self.reqs_cfg)

    def _get_image_urls(self) -> tuple[str, ...]:
        """
        Sends a GET request for image delivery metadata and
        returns contructed image URLs accordingly

        Reference:
            https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
        """
        r = self._get_with_ratelimit(
            f"{self.reqs_cfg["api_root"]}/at-home/server/{self.chapter.id}"
        )

        if (r_json := safe_to_json(r)) is None:
            raise ApiError(
                "Could not parse response into JSON for fetching image URLs", r
            )

        base_url = r_json["baseUrl"]
        chapter_hash = r_json["chapter"]["hash"]

        if self.img_cfg["use_datasaver"]:
            image_files = r_json["chapter"]["dataSaver"]
            quality = "data-saver"
        else:
            image_files = r_json["chapter"]["data"]
            quality = "data"
        # fmt: off
        expected_pages = get_cattributes(
            self.session, self.reqs_cfg, self.chapter)["pages"]
        # fmt: on
        if len(image_files) != expected_pages:
            logger.warning(
                "Possible missing pages for %s: "
                "Image links received: %s "
                "vs Expected pages in cattributes: %s",
                self.chapter.id,
                len(image_files),
                expected_pages,
            )

        return tuple(
            f"{base_url}/{quality}/{chapter_hash}/{file}" for file in image_files
        )

    ## Right now, MangaDex's reporting system seems to be down.
    ## According to some, it's been done for quite a while.
    ## - e.g. https://github.com/mansuf/mangadex-downloader/issues/146
    # def _send_image_report(  # pylint: disable=too-many-arguments too-many-positional-arguments
    #     self,
    #     image_url: str,
    #     success: bool,
    #     cached: bool,
    #     size_bytes: int,
    #     duration_ms: int,
    # ) -> None:  # pylint: enable=too-many-arguments too-many-positional-arguments
    #     """
    #     Sends a POST request to the MangaDex@Home report endpoint

    #     Reference:
    #         https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#the-mangadexhome-report-endpoint
    #     """
    #     if "mangadex.org" in image_url.split("/")[0]:  # base url
    #         return

    #     payload = {
    #         "url": image_url,
    #         "success": success,
    #         "bytes": size_bytes,
    #         "duration": duration_ms,
    #         "cached": cached,
    #     }
    #     logger.debug("Image report payload: %s", payload)
    #     try:
    #         requests.post(
    #             f"{self.reqs_cfg["report_endpoint"]}",
    #             json=payload,
    #             timeout=self.reqs_cfg["post_timeout"],
    #         )
    #         logger.info("Succesfully sent POST request for image reporting")
    #     except requests.Timeout:
    #         logger.warning("POST request timeout for image reporting exceeded")

    def _get_image_fp(self, idx: int, zeros: int, ext: str) -> Path:
        """
        Generates a filepath for an chapter's image (page) to be created in

        Args:
            idx (int): the page number, can start at 0
            zeros (int): the zero-padding to apply to all page numbers
            ext (str): the file extension, e.g. '.jpg'

        Returns:
            Path: where the image should be saved given its info
        """
        manga_title = self.manga_title[: self.save_cfg["max_title_length"]].strip()
        project_root = Path(__file__).resolve().parents[1]
        idx_zp = str(idx).zfill(zeros + 1)

        image_fp = Path(
            project_root / self.save_cfg["location"] / manga_title / f"{idx_zp}{ext}"
        )
        image_fp.parent.mkdir(parents=True, exist_ok=True)

        return image_fp

    def _download_image(self, url, fp: Path):
        c = pycurl.Curl()
        headers = []

        def header_func(line):
            headers.append(line.decode("iso-8859-1").strip())

        with fp.open("wb") as f:
            c.setopt(pycurl.URL, url)
            c.setopt(pycurl.WRITEDATA, f)
            c.setopt(pycurl.HEADERFUNCTION, header_func)

            try:
                c.perform()
                response_code = c.getinfo(pycurl.RESPONSE_CODE)
                success = 200 <= response_code < 300
                cached = any(h.lower().startswith("x-cache: hit") for h in headers)
                bytes_downloaded = c.getinfo(pycurl.SIZE_DOWNLOAD)
                duration_ms = c.getinfo(pycurl.TOTAL_TIME) * 1000
            except pycurl.error:
                success = False
                cached = False
                bytes_downloaded = 0
                duration_ms = 0
            finally:
                c.close()
        return (
            url,
            success,
            cached,
            bytes_downloaded,
            int(duration_ms),
        )

    def download_images(
        self, _retries: int | None = None, last_base_url: str | None = None
    ):
        """
        Downloads all images from the specified chapter.

        All images are saved under the configured save location
        under the manga title and chapter number.
        """
        # how many times to try getting a new base url
        if _retries is None:
            _retries = self.retry_cfg["max_retries"]

        logger.info("Downloading images. Retries left: %s", _retries)

        urls = self._get_image_urls()
        base_url = urls[0].split("/")[0]

        if base_url == last_base_url:
            logger.warning("Received same base URL upon failure")
            return

        zeros = len(str(len(urls)))

        for idx, url in enumerate(urls):
            ext = Path(url).suffix
            fp = self._get_image_fp(idx, zeros, ext)
            report = self._download_image(url, fp)
            if report[1] is not True:  # fail
                logger.warning("Failed to download image (success = %s)", report[1])
                self.download_images(_retries - 1, base_url)
            # self._send_image_report(*report)  Refer to READDME


if __name__ == "__main__":
    fake_cfg: Config = {
        "reqs": {
            "api_root": "https://api.mangadex.org",
            "report_endpoint": "https://api.mangadex.network/report",
            "get_timeout": 10,
            "post_timeout": 20,
        },
        "retry": {
            "max_retries": 5,
            "backoff_factor": 1,
            "backoff_jitter": 0.5,
            "backoff_max": 30,
        },
        "save": {"location": "mdex_save", "max_title_length": 60},
        "images": {"use_datasaver": False},
        "search": {"results_per_page": 10, "include_pornographic": False},
        "cli": {"options_per_row": 3, "use_ansi": True},
        "logging": {"enabled": True, "level": 20, "location": "logs"},
    }

    downloader = Downloader(
        Manga(
            "Makemasen kara to Iiharu Kao no Ii Onnanoko wo, Zenryoku de Kuppuku Saseru Yuri no Ohanashi",
            "6d2085c8-8340-4294-a8c8-ff0c213d4a05",
        ),
        Chapter("2e755b78-9447-4a77-aaa8-f3a2decfb9f2", "1"),
        fake_cfg,
    )

    downloader.download_images()
