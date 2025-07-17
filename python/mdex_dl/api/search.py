from mdex_dl.models import (Manga, Chapter, ApiError)

import requests
import time
from pathlib import Path


# SAVE = Path.joinpath(Path(__file__).parent, "mdex_save")
# ROOT = "https://api.mangadex.org"
# RESULTS_PER_PAGE = 10
# ZEROS = 3  # for zero padding image names


def api_check(r: requests.Response) -> None:
    """
    Checks health of API. Raise ApiError if things
    don't look good, else do nothing.

    - r is the API response that has NOT already
    been converted to a dict (with r.json())
    """
    try:
        result = r.json()["result"]
    except ValueError:
        raise ApiError(
            f"Something has gone VERY wrong. ({r.status_code})"
            f"API response: {r.text}")

    if result != "ok":
        raise ApiError(
            f"API returned result {result}, \
            expected 'ok'. Status code {r.status_code}")


def get_manga_title(attrs: dict) -> str:
    """
    Tries to retrieve title in en, if it fails
    it tries ja-ro and so on.
    """

    result = (
        attrs.get("title", {}).get("en")
        or attrs.get("title", {}).get("ja-ro")
        or attrs.get("title", {}).get("ja")
        or "Unknown Title"
    )

    return result


def search_manga(query: str, page: int = 0) -> list[Manga]:
    """
    Returns ten Manga objects according to relevance
    and page along with other parameters.
    """

    params = {
        "title": query,
        "order[relevance]": "desc",
        "hasAvailableChapters": "true",
        "offset": page * RESULTS_PER_PAGE,
        "limit": RESULTS_PER_PAGE
    }
    r = requests.get(f"{ROOT}/manga", params=params)  # type: ignore[arg-type]
    api_check(r)

    titles = []  # list[Manga]
    for manga in r.json()["data"]:
        manga_attrs = manga["attributes"]
        title = get_manga_title(manga_attrs)
        id = manga["id"]
        titles.append(Manga(title, id))

    return titles


# def image_report(img_url: str, success: bool, cached: bool,
#                  bytes: int, duration: int):
#     """
#     Reports successes and failures when loading images so MangaDex is happy.

#     Parameters:
#         img_url (str): The full URL of the image (including https://)
#         success (bool): True if the image was successfully retrieved
#         cached (bool): True if the server returned an X-Cache header with a
#                         value starting with HIT
#         bytes (int): The size (in bytes) of the retrieved image
#         duration (int): The time (in milliseconds) that the complete retrieval
#                         (not TTFB) of the image took

#     Reference:
#         https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
#     """
#     report_url = "https://api.mangadex.network/report"

#     report = {
#         "url": img_url,
#         "success": success,
#         "cached": cached,
#         "bytes": bytes,
#         "duration": duration
#     }
#     print(report)
#     requests.post(report_url, json=report)


# def download_chapter(chapter: Chapter, manga_title: str = "Unnamed"):
#     """
#     Downloads a chapter given a Chapter object.

#     Reference:
#         https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
#     """
#     r = requests.get(f"{ROOT}/at-home/server/{chapter.id}")
#     api_check(r)

#     r_json = r.json()
#     baseUrl = r_json["baseUrl"]  # str
#     hash = r_json["chapter"]["hash"]  # str
#     images = r_json["chapter"]["data"]  # list[str]

#     Construct page URLs and download
#     for page, image in enumerate(images, start=1):
#         Initialise vars. for report every iteration
#         url = ""
#         success = False
#         cached = False
#         bytes = 0
#         duration = 0

#         page_zp = str(page).zfill(ZEROS)  # zero-padded
#         url = f"{baseUrl}/data/{hash}/{image}"
#         ext = Path(url).suffix

#         img_path = Path(SAVE) / manga_title / chapter.title / f"{page_zp}{ext}"
#         img_path.parent.mkdir(parents=True, exist_ok=True)

#         start = time.time()

#         try:
#             r = requests.get(url, stream=True)
#         except requests.exceptions.RequestException as e:
#             end = time.time()
#             duration = round((end - start) * 1000)
#             image_report(url, success, cached, bytes, duration)
#             print(f"Error on file {url}: {e}")
#             continue

#         if r.headers.get("X-Cache", "").startswith("HIT"):
#             cached = True

#         try:
#             with open(img_path, "wb") as f:
#                 for chunk in r.iter_content(chunk_size=8192):
#                     bytes += len(chunk)
#                     f.write(chunk)
#             success = True
#         except Exception as e:
#             raise Exception(
#                 "Something went wrong while saving "
#                 f"file {url} in {img_path}: {e}") from e

#         end = time.time()
#         duration = round((end - start) * 1000)

#         image_report(url, success, cached, bytes, duration)
#         time.sleep(0.2)
