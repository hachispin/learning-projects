import requests
import time
from pathlib import Path


SAVE = Path.joinpath(Path(__file__).parent, "mdex_save")
ROOT = "https://api.mangadex.org"
RESULTS_PER_PAGE = 10


class Manga:
    """
    Parameters:
        title (str, required): The manga title as given by the API
        id (str, required): UUID used for GET requests
        tags (list[str], optional): list of genres used for searching
    """

    def __init__(self, title: str, id: str, tags: list[str] = [""]):
        self.title = title
        self.id = id
        self.tags = tags

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):
        return f"Manga('{self.title}', {self.id}, {self.tags})"


class Chapter:
    """
    Parameters:
        id (str): UUID used for GET requests
        chap_num (str | None): used to name dirs upon download

    self.title = Ch. {chap_num}
    """

    def __init__(self, id: str, chap_num):
        self.title = f"Ch. {chap_num}"
        self.id = id
        self.chap_num = chap_num  # May be None sadly

    def __str__(self):
        return self.title


class ApiError(Exception):
    """Exception raised for API problems"""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.message}"


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


def image_report(img_url: str, success: bool, cached: bool,
                 bytes: int, duration: int):
    """
    Reports successes and failures when loading images so MangaDex is happy.

    Parameters:
        img_url (str): The full URL of the image (including https://)
        success (bool): true if the image was successfully retrieved, false
                        otherwise
        cached (bool): true if the server returned an X-Cache header with a
                        value starting with HIT
        bytes (int): The size (in bytes) of the retrieved image
        duration (int): The time (in miliseconds) that the complete retrieval
                        (not TTFB) of the image took

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
    """
    report_url = "https://api.mangadex.network/report"

    report = {
        "url": img_url,
        "success": success,
        "cached": cached,
        "bytes": bytes,
        "duration": duration
    }
    print(report)
    requests.post(report_url, json=report)


def download_chapter(chapter: Chapter, manga_title: str = "Unnamed"):
    """
    Downloads a chapter given a Chapter object.

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
    """
    r = requests.get(f"{ROOT}/at-home/server/{chapter.id}")
    api_check(r)

    r_json = r.json()
    baseUrl = r_json["baseUrl"]  # str
    hash = r_json["chapter"]["hash"]  # str
    images = r_json["chapter"]["data"]  # list[str]

    # Construct page URLs and download
    for page, image in enumerate(images, start=1):
        # Initialise vars. for report every iteration
        url = ""
        success = False
        cached = False
        bytes = 0
        duration = 0

        url = f"{baseUrl}/data/{hash}/{image}"
        ext = Path(url).suffix

        img_path = Path(SAVE) / manga_title / chapter.title / f"{page}{ext}"
        img_path.parent.mkdir(parents=True, exist_ok=True)

        start = time.time()

        try:
            r = requests.get(url, stream=True)
        except requests.exceptions.RequestException as e:
            end = time.time()
            duration = round((end - start) * 1000)
            image_report(url, success, cached, bytes, duration)
            print(f"Error on file {url}: {e}")
            continue

        if r.headers.get("X-Cache", "").startswith("HIT"):
            cached = True

        try:
            with open(img_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    bytes += len(chunk)
                    f.write(chunk)
            success = True
        except Exception as e:
            raise Exception(
                "Something went wrong while saving "
                f"file {url} in {img_path}: {e}") from e

        end = time.time()
        duration = round((end - start) * 1000)

        image_report(url, success, cached, bytes, duration)
        # Adjust with caution (well not really, requests speed is atrocious)
        time.sleep(0.2)


def download_manga(manga: Manga, end: int, start: int = 0):
    """
    Downloads all chapters that fall in the range:
        start <= chap_num <= end

    Reference:
        https://api.mangadex.org/docs/04-chapter/retrieving-chapter/
    """

    if start > end:
        raise ValueError(
            f"Invalid range of chapters. Start {start} > End {end}")

    # Build chapters IDs within range
    chapters = []  # list[Chapter]

    r = requests.get(f"{ROOT}/manga/{manga.id}/feed")
    api_check(r)

    for chapter in r.json()["data"]:
        chap_id = chapter["id"]
        chap_num = chapter["attributes"]["chapter"]
        # I know you can just sort by languages, but for
        # some reason it only works if I do this (?)
        if chapter["attributes"]["translatedLanguage"] == "en":
            chapters.append(Chapter(chap_id, chap_num))

    for chapter in chapters:
        chap = chapter.chap_num
        if chap is None or not chap.replace(".", "").isdigit():
            continue
        if start <= float(chap) <= end:
            download_chapter(chapter, manga.title)


if __name__ == "__main__":

    def get_valid_index(prompt: str, max_index: int) -> int | None:
        user_input = input(prompt).strip()
        if user_input == "":
            return None
        if user_input.isdigit():
            val = int(user_input)
            if 1 <= val <= max_index:
                return val
        print("Going to next page...")
        return None

    search = input("Search for a manga in Romaji: ")
    page = 1

    while True:
        response = search_manga(search, page - 1)
        if not response:
            print("No manga found")
            exit()

        for i, manga in enumerate(response, start=1):
            print(f"[{i}]: {manga}")

        index = get_valid_index(
            "Enter manga index to download\n"
            "- Leave blank for next page\n"
            "Index: ", len(response))

        if index is None:
            page += 1
        else:
            chosen = response[index - 1]
            break

    start = int(input("What chapter to start download from? "))
    end = int(input("What chapter to stop downloading on? "))

    print("Querying...")
    download_manga(chosen, end, start)
    print("Done!")
