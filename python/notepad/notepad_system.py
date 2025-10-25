"""Contains the `Note` class and other note-related classes."""

import json
from pathlib import Path
import sys
from textwrap import dedent
import time
from datetime import datetime
from typing import override


# Note related exceptions
class NoteException(Exception):
    """Base class for all `Note` errors"""


class TitleAlreadyExistsError(NoteException):
    """
    Raised when a `Note` title conflicts with another
    note within a `NoteCollection` instance
    """

    def __init__(self, title: str):
        self.title: str = title
        super().__init__(f"Note with title '{title}' already exists")


class BlankBodyError(NoteException):
    """
    Raised when a `Note` instance is initialised
    with a blank (i.e, whitespace-only) `body`
    """


class BlankTitleError(NoteException):
    """
    Raised when a `Note` instance is initialised
    with a blank (i.e, whitespace-only) `title`
    """


class NotFoundError(NoteException):
    """
    Raised when attempting to perform a
    CRUD operation on a non-existent title
    of a `NoteCollection` instance
    """

    def __init__(self, title: str):
        self.title: str = title
        super().__init__(f"Note with title '{title}' not found")


class FormatError(NoteException):
    """
    Raised when (imported) note data has missing or blank keys or
    has the wrong format (e.g, ".txt" file extension instead of ".json")

    NOTE: Do not raise for empty data
    """


class Note:
    """
    Contains the fields:

    - `title` (str)
    - `body` (str)
    - `created_at` (str) [property]
    - `last_edited` (str)
    """

    def __init__(self, title: str, body: str, created_at: str, last_edited: str):
        if not title.strip():
            raise BlankTitleError()
        if not body.strip():
            raise BlankBodyError()

        self.title: str = title
        self.body: str = body
        self._created_at: str = created_at  # Private
        self.last_edited: str = last_edited

    @property
    def created_at(self):
        """Trivial getter for `created_at`."""
        return self._created_at

    @override
    def __repr__(self) -> str:
        return dedent(
            f"""\
            Note({repr(self.title)}, {repr(self.body)}, \
                {repr(self.created_at)}, {repr(self.last_edited)})\
        """
        )

    def to_dict(self) -> dict[str, str]:
        """Converts `self` to a `dict`, used for JSON conversions."""

        return {
            "title": self.title,
            "body": self.body,
            "created_at": self._created_at,
            "last_edited": self.last_edited,
        }  # Allows **kwargs for dict unpacking later

    @staticmethod
    def new(title: str, body: str) -> "Note":
        """
        Helper for creating a new note.
        This auto-fills the `created_at` and `last_edited` fields.
        """

        created_at = last_edited = datetime.now().isoformat()
        return Note(title, body, created_at, last_edited)


class NoteCollection:
    """A list of `Note` objects, uniquely identified by their titles"""

    def __init__(self, notes: list[Note]):
        self.notes: list[Note] = notes

    @override
    def __repr__(self) -> str:
        notes_repr = [repr(note) for note in self.notes]
        return f"NoteCollection({notes_repr})"

    def to_json(self) -> str:
        """Converts `self` to a JSON-formatted string."""
        notes_dict = [note.to_dict() for note in self.notes]
        return json.dumps({"NoteCollection": notes_dict}, indent=4)

    @property
    def all_titles(self) -> tuple[str, ...]:
        """Returns all notes' titles as a tuple."""
        return tuple(note.title for note in self.notes)

    def find_note_index(self, title: str) -> int:
        """Finds a note with the specified `title`, returns -1 if not found."""
        try:
            return self.all_titles.index(title)
        except ValueError:
            return -1  # Use this for raising errors

    # Consider using kwargs when calling this
    def edit_note(self, curr_title: str, new_title: str, new_body: str):
        """
        Given a `curr_title`,

        - attempt to find note with `curr_title`
        - if found, replace body with `new_body`
        - else, raise `NotFoundError`
        """

        idx = self.find_note_index(curr_title)

        if curr_title != new_title and new_title in self.all_titles:
            raise TitleAlreadyExistsError(new_title)
        if idx == -1:
            raise NotFoundError(curr_title)
        if not new_title.strip():
            raise BlankTitleError()
        if not new_body.strip():
            raise BlankBodyError()

        note = self.notes[idx]
        note.title = new_title
        note.body = new_body
        note.last_edited = datetime.now().isoformat()

    def add_note(self, note: Note):
        """
        Adds the given `note` if its title isn't
        taken, otherwise, raises `TitleAlreadyExistsError`.
        """

        if note.title not in self.all_titles:
            self.notes.append(note)
        else:
            raise TitleAlreadyExistsError(note.title)

    def delete_note(self, title: str):
        """
        Finds and deletes the note with the given `title`.

        Raises `NotFoundError` if note can't be found.
        """

        note_idx = self.find_note_index(title)
        if note_idx != -1:
            return self.notes.pop(note_idx)

        raise NotFoundError(title)

    @staticmethod
    def validate_json(fp: Path, strict: bool = True) -> None:
        """
        Given a Path `fp`:
            Checks if the file exists and has the ".json" suffix

        The `strict` flag checks existence of `NoteCollection`
        and each of its corresponding `Note` keys when True
        """

        if fp.suffix != ".json":
            raise FormatError(f"File provided must be '.json', not '{fp.suffix}'")
        if not fp.exists():
            raise FileNotFoundError(f"File '{fp}' does not exist")

        if not strict or fp.stat().st_size == 0:
            return  # Do not error on empty data

        # Only ran iff strict=True
        with fp.open() as f:
            data = json.load(f)  # pyright: ignore[reportAny]
            req_note_keys = ("title", "body", "created_at", "last_edited")
            collection = data.get("NoteCollection")  # pyright: ignore[reportAny]

            if collection is None:
                raise FormatError(
                    "Missing top level NoteCollection key (file is not empty)"
                )

            if not isinstance(collection, list):
                t = type(  # pyright: ignore[reportUnknownVariableType]
                    collection  # pyright: ignore[reportAny]
                )
                raise FormatError(f"Expected list for NoteCollection, instead got {t}")

            # fmt: off
            for note in collection:  # pyright: ignore[reportUnknownVariableType]
                if not all(
                    note.get(key) for key in req_note_keys  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType] pylint: disable[line-too-long]
                ):
                    raise FormatError("Missing or blank Note keys")
            # fmt: on
        return

    @staticmethod
    def write_to_json(collection: "NoteCollection", fp: Path):
        """Writes `self` as JSON to the given path `fp`."""

        # Non-strict - Only checks fp exists and is json
        NoteCollection.validate_json(fp, strict=False)
        with fp.open("w") as f:
            f.write(collection.to_json())

    @staticmethod
    def from_json(fp: Path) -> "NoteCollection":
        """Creates a `NoteCollection` instance from the given JSON from path `fp`."""

        NoteCollection.validate_json(fp)

        with fp.open() as f:
            if not f.readline():  # Empty
                return NoteCollection([])

            f.seek(0)
            notes_dict = json.load(f)["NoteCollection"]  # pyright: ignore[reportAny]

        notes = [Note(**note) for note in notes_dict]  # pyright: ignore[reportAny]
        return NoteCollection(notes)


if __name__ == "__main__":  # Create test notes
    ans = input("Overwrite save with test cases? (Y/N): ")
    if ans.strip().lower() != "y":
        sys.exit(0)

    new = NoteCollection(
        [
            Note.new("Test Note", "A placeholder body"),
            Note.new("Another One", "You see me?"),
        ]
    )

    time.sleep(3)
    new.edit_note(
        curr_title="Another One",  # Used to find index
        new_title="Changed Title",
        new_body="hi",
    )

    new_json = new.to_json()
    print(new_json)

    save = Path.joinpath(Path(__file__).parent, "data.json")
    with save.open("w", encoding="utf-8") as save_stream:
        save_stream.write(new_json)

    print(NoteCollection.from_json(save))
