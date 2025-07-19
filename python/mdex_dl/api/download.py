import logging
from io import BytesIO
from pathlib import Path

import requests
import pycurl
import certifi

from mdex_dl.models import Chapter, Manga
from mdex_dl.utils import require_ok_json, get_cattributes
from mdex_dl.load_config import Config

# NOTE: Downloader class instances are created for
# each chapter, and not for the entire manga


class Downloader:
    """
    A class that wraps fetching, downloading and saving functionality
    for a specified `Chapter` object
    """

    def __init__(self, manga: Manga, chapter: Chapter, config: Config):
        logging.debug("Created Downloader() instance with chapter id: %s", chapter.id)

        # fmt: off
        self.api_root               = config["reqs"]["api_root"]
        self.report_endpoint        = config["reqs"]["report_endpoint"]
        self.max_retries            = config["reqs"]["max_retries"]
        self.base_delay             = config["reqs"]["base_delay"]
        self.base_delay_ratelimit   = config["reqs"]["base_delay_ratelimit"]
        self.get_timeout            = config["reqs"]["get_timeout"]  # for GET requests
        self.post_timeout           = config["reqs"]["post_timeout"]
        self.use_datasaver          = config["images"]["use_datasaver"]
        self.save_location          = config["save"]["location"]
        # fmt: on

        self.chapter = chapter

    def get_image_urls(self, datasaver: bool) -> tuple[str, ...]:
        """
        Sends a GET request for image delivery metadata and
        returns contructed image URLs accordingly

        Reference:
            https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
        """
        r = requests.get(
            f"{self.api_root}/at-home/server/{self.chapter.id}",
            timeout=self.get_timeout,
        )
        r_json = require_ok_json(r)

        base_url = r_json["baseUrl"]
        chapter_hash = r_json["chapter"]["hash"]

        if datasaver:
            image_files = r_json["chapter"]["dataSaver"]
            quality = "data-saver"
        else:
            image_files = r_json["chapter"]["data"]
            quality = "data"

        expected_pages = get_cattributes(self.api_root, self.chapter)["pages"]
        if len(image_files) != expected_pages:
            logging.warning(
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

    def send_image_report(
        self,
        image_url: str,
        success: bool,
        cached: bool,
        size_bytes: int,
        duration_ms: int,
    ) -> None:
        """
        Sends a POST request to the MangaDex@Home report endpoint

        Reference:
            https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#the-mangadexhome-report-endpoint
        """
        payload = {
            "url": image_url,
            "success": success,
            "bytes": size_bytes,
            "duration": duration_ms,
            "cached": cached,
        }

        r = requests.post(
            f"{self.report_endpoint}", json=payload, timeout=self.image_report_timeout
        )

    def download_images(self): ...


if __name__ == "__main__":  # Tests
    # Just a fake config for testing
    cfg = {"api_root": "https://api.mangadex.org", "save": {"root": "mdex_save"}}

    c = Chapter(id="a54c491c-8e4c-4e97-8873-5b79e59da210", chap_num=1)
    d = Downloader(c, cfg)
    print(d.image_urls)


# def download_manga(manga: Manga, end: int, start: int = 0):
#     """
#     Downloads all chapters that fall in the range:
#         start <= chap_num <= end

#     Reference:
#         https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
#     """

#     if start > end:
#         raise ValueError(
#             f"Invalid range of chapters. Start {start} > End {end}")

#     # Build chapters IDs within range
#     chapters = []  # list[Chapter]

#     r = requests.get(f"{ROOT}/manga/{manga.id}/feed")
#     api_check(r)

#     for chapter in r.json()["data"]:
#         chap_id = chapter["id"]
#         chap_num = chapter["attributes"]["chapter"]
#         # I know you can just sort by languages, but for
#         # some reason it only works if I do this (?)
#         if chapter["attributes"]["translatedLanguage"] == "en":
#             chapters.append(Chapter(chap_id, chap_num))

#     for chapter in chapters:
#         chap = chapter.chap_num
#         if chap is None or not chap.replace(".", "").isdigit():
#             continue
#         if start <= float(chap) <= end:
#             download_chapter(chapter, manga.title)
