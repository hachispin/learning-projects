from mdex_dl.models import Chapter

import requests
import pycurl
import certifi
from io import BytesIO


class Downloader:
    def __init__(self, config: dict):
        self.root = config["api_root"]
        self.save_loc = config["save"]["root"]

    def get_image_urls(self, chapter: Chapter,
                       datasaver: bool) -> tuple[str, ...]:
        """
        Reference:
            https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
        """

        r = requests.get(f"{self.root}/at-home/server/{chapter.id}")
        r_json = r.json()

        base_url = r_json["baseUrl"]
        chapter_hash = r_json["chapter"]["hash"]

        if datasaver:
            image_files = r_json["chapter"]["dataSaver"]
            quality = "data-saver"
        else:
            image_files = r_json["chapter"]["data"]
            quality = "data"

        return tuple(
            f"{base_url}/{quality}/{chapter_hash}/{file}"
            for file in image_files
        )

    def send_image_report(self,
                          image_url: str, success: bool, cached: bool,
                          size_bytes: int, duration: int):
        """
        Sends a POST request to the MangaDex@Home report endpoint

        Reference:
            https://api.mangadex.org/docs/04-chapter/retrieving-chapter/#the-mangadexhome-report-endpoint
        """

    def download_images(self, *image_urls: str): ...


if __name__ == "__main__":  # Tests
    # Just a fake config for testing
    cfg = {
        "api_root": "https://api.mangadex.org",
        "save": {"root": "mdex_save"}
    }

    d = Downloader(cfg)
    c = Chapter(id="a54c491c-8e4c-4e97-8873-5b79e59da210", chap_num=1)
    print(d.get_image_urls(c, datasaver=True))


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

if __name__ == "__main__":
    raise RuntimeError(
        "run this file as a module: python -m mdex_dl.api.download")
