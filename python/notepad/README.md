## Description

A rudimentary note-saving app with data persistence and simple CRUD operations.  
You must have the [PyQt6](https://pypi.org/project/PyQt6/) library installed to use this.

## Usage

Notes are stored in `data.json` (as of now, this can't be directly configured). This file will be created upon first use.

- Viewing a note is done through the dropdown (`QComboBox`)
- Saving and deleting are done through the "Save" and "Delete" buttons
- Editing is also done through the "Save" button after choosing a note from the dropdown

## To-do

- Convert the pseudo-menubar into an actual menubar with `QMenuBar`
- Allow imports and exports of note data
- Toggle between plain view and HTML view (?)
- Change note viewing from using `QComboBox` to possibly a `QListView`
- Add note searching and possibly filters (e.g., most recently edited)
