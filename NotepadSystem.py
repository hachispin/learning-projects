import json
from pathlib import Path
import time
from datetime import datetime


# Note related exceptions
class NoteException(Exception):
    """Base class for all Note errors"""
    pass


class TitleAlreadyExistsError(NoteException):
    """
    Raised when a `Note` title conflicts with another
    note within a `NoteCollection` instance
    """

    def __init__(self, title):
        self.title = title
        super().__init__(f"Note with title '{title}' already exists")


class BlankBodyError(NoteException):
    """
    Raised when a Note instance is initialised
    with a blank (i.e, whitespace-only) `body`
    """
    pass


class BlankTitleError(NoteException):
    """
    Raised when a `Note` instance is initialised
    with a blank (i.e, whitespace-only) `title`
    """
    pass


class NotFoundError(NoteException):
    """
    Raised when attempting to perform a
    CRUD operation on a non-existent title
    of a `NoteCollection` instance
    """

    def __init__(self, title):
        self.title = title
        super().__init__(f"Note with title '{title}' not found")


class FormatError(NoteException):
    """
    Raised when (imported) note data has missing or blank keys or
    has the wrong format (e.g, .txt file extension instead of .json)

    NOTE: Do not raise for empty data
    """
    pass


class Note:
    def __init__(self, title, body, created_at, last_edited):
        if not title.strip():
            raise BlankTitleError()
        if not body.strip():
            raise BlankBodyError()

        self.title = title
        self.body = body
        self._created_at = created_at  # Private
        self.last_edited = last_edited

    @property
    def created_at(self):
        return self._created_at

    def __repr__(self) -> str:
        return "Note('{}', '{}', '{}', '{}')".format(
            self.title,
            self.body,
            self.created_at,
            self.last_edited
        )

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "created_at": self._created_at,
            "last_edited": self.last_edited
        }  # Allows **kwargs for dict unpacking later

    @staticmethod
    def new_note(title, body) -> "Note":
        created_at = last_edited = datetime.now().isoformat()
        return Note(title, body, created_at, last_edited)


class NoteCollection:
    """A list of `Note` objects, uniquely identified by their titles"""

    def __init__(self, notes: list[Note]):
        self.notes = notes

    def __repr__(self) -> str:
        notes_repr = [repr(note) for note in self.notes]
        return f"NoteCollection({notes_repr})"

    def to_json(self) -> str:
        notes_dict = [note.to_dict() for note in self.notes]
        return json.dumps({"NoteCollection": notes_dict}, indent=4)

    @property
    def all_titles(self) -> tuple[str, ...]:
        return tuple(note.title for note in self.notes)

    def find_note_index(self, title) -> int:
        try:
            return self.all_titles.index(title)
        except ValueError:
            return -1  # Use this for raising errors

    # Consider using kwargs when calling this
    def edit_note(self, curr_title, new_title, new_body):
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
        if note.title not in self.all_titles:
            self.notes.append(note)
        else:
            raise TitleAlreadyExistsError(note.title)

    def delete_note(self, title):
        note_idx = self.find_note_index(title)
        if note_idx != -1:
            return self.notes.pop(note_idx)

        raise NotFoundError(title)

    @staticmethod
    def validate_json(fp: Path, strict=True) -> None:
        """
        Given a Path `fp`:
            Checks if the file exists and has the `.json` suffix

        The `strict` flag checks existence of `NoteCollection`
        and each of its corresponding `Note` keys when True
        """

        if fp.suffix != ".json":
            raise FormatError(
                f"File provided must be '.json', not '{fp.suffix}'")
        if not fp.exists():
            raise FileNotFoundError(f"File '{fp}' does not exist")

        if not strict or fp.stat().st_size == 0:
            return  # Do not error on empty data

        # Only ran iff strict=True
        with fp.open() as f:
            data = json.load(f)
            req_note_keys = ("title", "body", "created_at", "last_edited")
            collection = data.get("NoteCollection")

            if collection is None:
                raise FormatError(
                    "Missing top level NoteCollection key (file is not empty)")

            if not isinstance(collection, list):
                t = type(collection)
                raise FormatError(
                    f"Expected list for NoteCollection, instead got {t}"
                )

            for note in collection:
                if not all(note.get(key) for key in req_note_keys):
                    raise FormatError("Missing or blank Note keys")
        return

    @staticmethod
    def write_to_json(collection: "NoteCollection", fp: Path):
        # Non-strict - Only checks fp exists and is json
        NoteCollection.validate_json(fp, strict=False)
        with fp.open("w") as f:
            f.write(collection.to_json())

    @staticmethod
    def from_json(fp: Path) -> "NoteCollection":
        NoteCollection.validate_json(fp)

        with fp.open() as f:
            if not f.readline():  # Empty
                return NoteCollection([])

            f.seek(0)
            notes_dict = json.load(f)["NoteCollection"]

        notes = [Note(**note) for note in notes_dict]
        return NoteCollection(notes)


if __name__ == "__main__":  # Create test notes
    ans = input("Overwrite save with test cases? (Y/N): ")
    if ans.strip().lower() != "y":
        exit()

    new = NoteCollection([
        Note.new_note("Test Note", "A placeholder body"),
        Note.new_note("Another One", "You see me?")
    ])

    time.sleep(3)
    new.edit_note(
        curr_title="Another One",  # Used to find index
        new_title="Changed Title",
        new_body="hi"
    )

    new_json = new.to_json()
    print(new_json)

    fp = Path.joinpath(Path(__file__).parent, "data.json")
    with fp.open("w", encoding="utf-8") as f:
        f.write(new_json)

    print(NoteCollection.from_json(fp))
