from enum import Enum


class Manga:
    """
    Parameters:
        title (str, required): The manga title as given by the API
        id (str, required): UUID used for GET requests
        tags (list[str], optional): list of genres used for searching
    """

    def __init__(self, title: str, id: str, tags: list[str] | None = None):
        self.title = title
        self.id = id
        self.tags = tags

    def __str__(self):
        return f"{self.title}"

    def __repr__(self):   # ↓ repr() is used to handle quotes in strings
        repr_str = f"Manga({repr(self.title)}, {repr(self.id)}"

        if self.tags:
            repr_str += f", {repr(self.tags)}"

        return repr_str


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
        self.chap_num = chap_num

    def __repr__(self) -> str:
        return f"{repr(self.id)}"

    def __str__(self):
        return self.title


class ApiError(Exception):
    """Exception raised for API problems"""

    def __init__(self, message):
        super().__init__(message)


class ConfigError(Exception):
    """Exception raised for unrecoverable config states"""

    def __init__(self, message: str, bad_options: list[str]):
        super().__init__(message)
        self.bad_options = bad_options

    def __str__(self):
        return f"{self.args[0]} - Bad options: {self.bad_options}"
