# cli-keepass

Python script focused on Linux console, to be a cli to access a keepass db/file. There is no required for a GUI, as this is all text base

## Requirements
- 3.10 or greater (Only tested on 3.12)

Third party libs

- pykeepass == 4.1.1.post1
- prompt_toolkit

# General Info

Navigating in the cli is similiar to navigating a directory. Commands like cd are used to change into groups (like directories), and ls to list the entries in the group.


# What's supported
This is just supporting the raw basics. Entries only have the following fields, `Title`, `User`, `Password`, `URL`, and `Notes`. Attachments, custom attributes, icons, and anything other fields are unable to be displayed, added, or changed. Groups can have sub groups, though the only fields supported for them are `Name` and `Notes`.
