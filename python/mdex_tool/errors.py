"""
Contains all subclassed exceptions used
"""

from typing import override
from requests import Response


class ApiError(Exception):
    """
    Exception raised for API problems, such
    as a non-ok result in a response body
    """

    def __init__(self, message: str, response: Response | None = None):
        super().__init__(message)
        self.response: Response | None = response


class ConfigError(Exception):
    """Exception raised for bad config states"""

    def __init__(self, errors: list[str]):
        super().__init__()
        self.errors: list[str] = errors

    @override
    def __str__(self):
        return "Config validation failed:\n" + "\n".join(
            f"- {err}" for err in self.errors
        )
