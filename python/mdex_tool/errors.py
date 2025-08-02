"""
Contains all subclassed exceptions used
"""

from requests import Response


class ApiError(Exception):
    """
    Exception raised for API problems, such
    as a non-ok result in a response body
    """

    def __init__(self, message, response: Response | None = None):
        super().__init__(message)
        self.response = response


class ConfigError(Exception):
    """Exception raised for bad config states"""

    def __init__(self, errors: list[str]):
        self.errors = errors

    def __str__(self):
        return "Config validation failed:\n" + "\n".join(
            f"- {err}" for err in self.errors
        )
