"""
Contains all classes and subclassed exceptions
that are used in other modules.

Note that no functionality is here; common
functions instead are in `mdex_dl.utils`
"""


class Manga:
    """
    Parameters:
        title (str, required): the manga title as given by the API
        id (str, required): UUID used for GET requests
        tags (list[str], optional): list of genres used for searching
    """

    def __init__(self, title: str, uuid: str, tags: list[str] | None = None):
        self.title = title
        self.id = uuid
        self.tags = tags

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):  # ↓ repr() is used to handle quotes in strings
        repr_str = f"Manga({repr(self.title)}, {repr(self.id)}"

        if self.tags:
            repr_str += f", {repr(self.tags)}"

        return repr_str


class Chapter:
    """
    Parameters:
        id (str): UUID used for GET requests
        chap_num (str | None): used to name dirs upon download
    """

    def __init__(self, uuid: str, chap_num: str | None):
        self.title = f"Ch. {chap_num or "Unknown"}"
        self.id = uuid
        self.chap_num = chap_num

    def __repr__(self) -> str:
        return f"{repr(self.id)}"

    def __str__(self):
        return self.title
