"""
Contains the Downloader() class.

NOTE: Downloader class instances are created for
each chapter, and not for the entire manga
"""

import logging
from pathlib import Path

# pylint:disable=c-extension-no-member
import requests
import pycurl

from mdex_dl import PROJECT_ROOT
from mdex_dl.errors import ApiError
from mdex_dl.models import Chapter, Manga, Config, ChapterGetResponse, ImageReport
from mdex_dl.api.http_config import get_retry_adapter
from mdex_dl.api.client import (
    get_with_ratelimit,
    get_cattributes,
    safe_to_json,
    assert_ok_response,
)

logger = logging.getLogger(__name__)


class Downloader:
    """
    Wraps fetching, downloading and saving functionality for
    a specified `Chapter` object, following config rules.
    """

    def __init__(self, manga: Manga, chapter: Chapter, cfg: Config):
        logger.debug("Created Downloader() instance with chapter id: %s", chapter.uuid)

        # Create session binded to Retry() logic
        self.session = requests.session()
        adapter = get_retry_adapter(cfg.retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.cfg = cfg
        self.chapter = chapter
        self.manga_title = manga.title[: self.cfg.save.max_title_length]

    def __repr__(self):
        # Full Manga object isn't included because only the title is saved
        return f"Downloader(Manga({self.manga_title}, ...), {self.chapter})"

    def _get_with_ratelimit(self, url: str):
        """Packages get_with_ratelimit() from .api.client into a method"""
        return get_with_ratelimit(url, self.session, self.cfg)

    def _send_chapter_get(self) -> ChapterGetResponse:
        r = self.session.get(
            f"{self.cfg.reqs.api_root}/at-home/server/{self.chapter.uuid}",
            timeout=self.cfg.reqs.get_timeout,
        )

        if (r_json := safe_to_json(r)) is None:
            raise ApiError(
                "Could not convert `GET /at-home/server/:chapterId` "
                "response from _send_chapter_get() to JSON",
                r,
            )
        assert_ok_response(r_json)

        try:
            cdn_data = {
                "base_url": r_json["baseUrl"],
                "chapter_hash": r_json["chapter"]["hash"],
                "filenames_data": tuple(r_json["chapter"]["data"]),
                "filenames_data_saver": tuple(r_json["chapter"]["dataSaver"]),
            }
        except KeyError:
            raise ApiError(
                "Missing keys for `GET /at-home/server/:chapterId` "
                "response from _send_chapter_get()",
                r,
            ) from None
        logger.debug("`GET /at-home/server/:chapterId` CDN data: %s", cdn_data)
        chapter_get = ChapterGetResponse(**cdn_data)

        cattrs = get_cattributes(self.session, self.cfg.reqs, self.chapter)

        if len(chapter_get.filenames_data) != cattrs["pages"]:
            logger.warning(
                "Possible missing pages: number of image URLs "
                "vs pages in chapter attributes = %s, %s",
                len(chapter_get.filenames_data),
                cattrs["pages"],
            )

        return ChapterGetResponse(**cdn_data)

    def _construct_image_urls(self, cdn_data: ChapterGetResponse) -> tuple[str, ...]:
        if self.cfg.images.use_datasaver:
            quality = "data-saver"
            filenames = cdn_data.filenames_data_saver
        else:
            quality = "data"
            filenames = cdn_data.filenames_data

        cdn_url = f"{cdn_data.base_url}/{quality}/{cdn_data.chapter_hash}/"

        return tuple(cdn_url + f for f in filenames)

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
        idx_zp = str(idx).zfill(zeros + 1)

        image_fp = Path(
            PROJECT_ROOT / self.cfg.save.location / self.manga_title / f"{idx_zp}{ext}"
        )
        image_fp.parent.mkdir(parents=True, exist_ok=True)

        return image_fp

    def _get_image_stats(
        self, url: str, headers: list[str], c: pycurl.Curl
    ) -> ImageReport:
        response_code = c.getinfo(pycurl.RESPONSE_CODE)

        stats = {
            "url": url,
            "success": 200 <= response_code < 300,
            "cached": any(h.lower().startswith("x-cache: hit") for h in headers),
            "size_bytes": c.getinfo(pycurl.SIZE_DOWNLOAD),
            "duration_ms": c.getinfo(pycurl.TOTAL_TIME) * 1000,
        }

        logger.debug("ImageReport for chapter '%s': %s", self.chapter.uuid, stats)
        return ImageReport(**stats)

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
                stats = self._get_image_stats(url, headers, c)

            except pycurl.error as e:
                logger.warning("Encountered PyCurl error: %s", e)
                stats = ImageReport(  # error sentinels
                    url,
                    False,
                    False,
                    0,
                    0,
                )
            finally:
                c.close()

        return stats

    def _download_images(
        self, retries: int | None, last_base_url: str | None, img_idx=0
    ):
        """
        Downloads all images from the specified chapter.

        All images are saved under the configured save location
        under the manga title and chapter number.
        """
        # how many times to try getting a new base url
        if retries is None:
            retries = self.cfg.retry.max_retries

        logger.info("Downloading images. Retries left: %s", retries)

        cdn_data = self._send_chapter_get()
        base_url = cdn_data.base_url
        if base_url == last_base_url:
            logger.warning("Received same base URL upon failure")
            return

        urls = self._construct_image_urls(cdn_data)
        zeros = len(str(len(urls))) + 1  # +1 purely for looks

        for idx, url in enumerate(urls[img_idx:]):  # start from where we last left off
            ext = Path(url).suffix
            fp = self._get_image_fp(idx, zeros, ext)
            report = self._download_image(url, fp)
            if report.success is not True:
                logger.warning(
                    "Failed to download image (success = %s)", report.success
                )
                self._download_images(retries - 1, base_url, idx)
            # self._send_image_report(*report)
            # ^ Check ahead for why this is commented out!

    def download_images(self):
        """
        Downloads all images from the stored chapter.

        All images are saved under the configured save
        location, manga title and chapter number.
        """
        self._download_images(retries=None, last_base_url=None)

    ## Right now, MangaDex's reporting system seems to be down, according to
    ## my and others' experiences, so this function will remain unused for now.
    ## here's an example: https://github.com/mansuf/mangadex-downloader/issues/146

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
    #         https://api.mangadex.org/docs/04-chapter/retrieving-chapter
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
