"""The entry point, which also contains the PyQt6 GUI code."""

import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QSize  # pylint: disable=no-name-in-module
from PyQt6.QtGui import QBrush  # pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,  # pylint: disable=no-name-in-module
    QMainWindow,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QWidget,
    QMessageBox,
    QSizePolicy,
)

from notepad.notepad_system import (
    Note,
    NoteCollection,
    NoteException,
    TitleAlreadyExistsError,
    BlankTitleError,
    BlankBodyError,
    NotFoundError,
    FormatError,
)


SAVE_NAME = "data.json"  # must be json
APP_DIR = Path(__file__).parent
NOTES_DATA = Path.joinpath(APP_DIR, SAVE_NAME)

if not APP_DIR.exists():
    raise FileNotFoundError("Could not find parent dir")

if not NOTES_DATA.exists():
    NOTES_DATA.write_text("", encoding="utf-8")


class MainWindow(QMainWindow):
    """Main window for notepad."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("notepad")  # Should consider a better name soon
        self.setMinimumSize(QSize(640, 360))

        self.collection: NoteCollection = self.load_data()
        menubar = QHBoxLayout()
        top = QVBoxLayout()

        # Menubar
        self.curr_note_title: QLineEdit = QLineEdit()
        self.curr_note_title.setPlaceholderText("New title")
        self.curr_note_title.setMaxLength(24)
        self.curr_note_title.setFixedWidth(280)
        self.dropdown: QComboBox = QComboBox()
        self.save: QPushButton = QPushButton("Save")
        self.delete: QPushButton = QPushButton("Delete")

        least_width = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.save.setSizePolicy(least_width)
        self.delete.setSizePolicy(least_width)
        menubar.addWidget(self.curr_note_title)
        menubar.addWidget(self.dropdown)
        menubar.addWidget(self.save)
        menubar.addWidget(self.delete)
        self.update_dropdown()

        # Body, not set until note picked
        self.curr_note_body: QTextEdit = QTextEdit()
        self.curr_note_body.setPlaceholderText("Start writing a new note here...")

        # Mappings, note that (dropdown_index - 1) = NoteCollection_index
        self.dropdown.currentIndexChanged.connect(self.display_note)
        self.save.clicked.connect(self.save_curr_note)
        self.delete.clicked.connect(self.delete_curr_note)
        # Layout
        top.addLayout(menubar)
        top.addWidget(self.curr_note_body)
        container = QWidget()
        self.setCentralWidget(container)
        container.setLayout(top)

    def handle_exception(self, error: Exception):
        """
        Generic exception handler.

        If `error` is not a `NoteException` instance, a message
        box is displayed and `sys.exit()` is called afterwards.
        """
        if isinstance(error, NoteException):
            self.handle_note_exception(error)

        error_type = type(error).__name__
        error_help = str(error)

        QMessageBox.critical(
            self,
            f"Unexpected {error_type}",
            f"{error_help}\n\nPress any button to exit...",
        )

        sys.exit(1)

    def handle_note_exception(self, error: NoteException):
        """Provides a message box detailing the `error`, which is a `NoteException`."""
        match error:
            case TitleAlreadyExistsError():
                QMessageBox.warning(self, "Save failed", "This title is already taken.")
            case BlankTitleError():
                QMessageBox.warning(self, "Invalid title", "Title must not be blank.")
            case BlankBodyError():
                QMessageBox.warning(
                    self, "Invalid body", "Note body must not be blank."
                )
            case NotFoundError():
                QMessageBox.warning(
                    self, "Note not found", "Could not find note to read/update/delete"
                )
            case FormatError():
                QMessageBox.warning(
                    self, "Invalid import", "Imported notes format could not be read"
                )
            case _:  # should be unreachable
                raise error

    def load_data(self) -> NoteCollection:
        """Parses `NOTES_DATA` and returns a `NoteCollection`."""

        return NoteCollection.from_json(NOTES_DATA)

    def save_notes(self):
        """Writes the currently stored `NoteCollection` to `NOTES_DATA`."""
        NoteCollection.write_to_json(self.collection, NOTES_DATA)

    def get_note_by_dropdown(self, dd_idx: int | None = None) -> Note:
        """Returns the Note object at current or chosen dropdown index"""

        if dd_idx is None:
            dd_idx = self.dropdown.currentIndex()

        elif dd_idx == 0:
            e = ValueError("Attempted to access reserved index 0 (New note...)")
            self.handle_exception(e)

        try:
            return self.collection.notes[dd_idx - 1]
        except IndexError as e:
            num_notes = len(self.collection.notes)
            num_dd_items = self.dropdown.count()
            info = f"num_notes={num_notes}, num_dd_items={num_dd_items}"
            e = IndexError(f"Index ({dd_idx} - 1) out of notes ({info})")

            self.handle_exception(e)

    def update_dropdown(self):
        """Updates dropdown items with stored notes"""
        dd = self.dropdown

        # Set "New note..." to gray for UX
        dd.clear()
        dd.addItem("New note...")
        idx = dd.model().index(0, 0)  # pyright: ignore[reportOptionalMemberAccess]
        dd.model().setData(  # pyright: ignore[reportOptionalMemberAccess]
            idx, QBrush(Qt.GlobalColor.gray), Qt.ItemDataRole.ForegroundRole
        )

        self.dropdown.addItems([note.title for note in self.collection.notes])

    def display_note(self):
        """
        Update UI to show chosen Note title and body
        according to current dropdown index
        """
        title_ui = self.curr_note_title
        body_ui = self.curr_note_body
        idx = self.dropdown.currentIndex()

        if idx > 0:  # Load Note title, body
            note = self.get_note_by_dropdown()

            title_ui.setText(note.title)
            body_ui.setPlainText(note.body)
        else:
            title_ui.setText("")
            body_ui.setPlainText("")

    def save_curr_note(self):
        """
        Saves the current note being written by the user.

        If "saving" is invoked on an already-existing
        note, its equivalent to an "edit" of that note.
        """
        saved_title = self.curr_note_title.text().strip()
        saved_body = self.curr_note_body.toPlainText().strip()
        curr = self.dropdown.currentIndex()

        try:
            if curr == 0:  # Add
                new = Note.new(saved_title, saved_body)
                self.collection.add_note(new)
            else:  # Edit
                curr_note = self.get_note_by_dropdown(curr)
                self.collection.edit_note(curr_note.title, saved_title, saved_body)

        except NoteException as e:
            self.handle_note_exception(e)
            return

        # Reflect changes in save data
        self.save_notes()
        self.update_dropdown()
        self.display_note()
        return

    def delete_curr_note(self):
        """
        Deletes the current note being displayed to the user.

        If the "note" hasn't been saved yet, the body and title are cleared.
        """

        title = self.curr_note_title
        body = self.curr_note_body

        if self.dropdown.currentIndex() == 0:
            title.setText("")
            body.setPlainText("")
        else:
            self.collection.delete_note(title.text())
            self.save_notes()
            self.update_dropdown()


notepad = QApplication([])
window = MainWindow()
window.show()
notepad.exec()
