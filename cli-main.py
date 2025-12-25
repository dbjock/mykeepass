import os
import argparse
import getpass
from pathlib import Path
import logging
import logging.config
import tomllib
import traceback
import uuid

# External libs
from pykeepass import PyKeePass
from pykeepass import exceptions as pkExceptions

# CLI libs
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import CompleteStyle, print_formatted_text,confirm,choice
from prompt_toolkit.filters import is_done
from prompt_toolkit.formatted_text import FormattedText, HTML
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.styles import Style

# Setting THIS logger to be the root
logger = logging.getLogger('main-cli')

mainStyles = Style.from_dict({
    'fldname': '#276CF5',
    'green': '#27F5B0',
    'red': '#F54927',
    'frame.border': '#884444',
    "promptfield": 'bold underline',
    })

# Command builder to help user
cmdHelper = {
    'help': {
        'add': None,
        'chggrp': None,
        'chgpwd': None,
        'cd': None,
        'delete': None,
        'edit': None,
        'find': None,
        'getpass': None,
        'list': None,
        'show': None,
        'exit': None,
        'quit': None,
    },
    'add': {
        'entry': None,
        'group': None,
    },
    'chggrp': None,
    'chgpwd': None,
    'cd' : None,
    'delete': {
        'entry': None,
        'group': None,
    },
    'edit': {
        'entry': None,
        'group': None,
    },
    'find': {
        'entry': {
            'title': None,
            'username': None
        },
        'group': None,
    },
    'getpass': None,
    'show':  {
        'entry': None,
        'group': None,
    },
    'exit': None,
    'quit': None,
    'list': None,
    'ls': None,
}
GBLSettings = {'currentGrp': None }

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def addEntry() -> tuple:
    """Prompts user for values for the various fields to add an entry

    Returns:
        tuple:
            status (bool):
                True - Entry saved in db, and Entry is in next element
                False - Entry was not saved. None is next element
            Entry | None:
                If status is True this will have the Entry, else None
    """
    print("Adding a new entry")
    logger.debug("Adding a new entry")
    entrySession = PromptSession()

    logger.info('Prompt user for entry title')
    while True:
        try:
            entry_title = entrySession.prompt(message='Title > ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm(msg="Cancel Adding Entry "):
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new entry title
                pass
        else:
            break
    logger.info(f"entry_title={entry_title!r}")

    logger.info('Prompt user for entry group/path')
    while True:
        try:
            # Have user choose, default choice is the current group they are in
            entry_group = groupChoices(grpUUID=GBLSettings['currentGrp'].uuid)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Entry "):
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new group's parent group
                pass
        else:
            break

    logger.info(f"Group chosen: {entry_group}")

    logger.info('Prompt user for entry username')
    while True:
        try:
            entry_username = entrySession.prompt(message='User name > ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Entry "):
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new entry username
                pass
        else:
            break
    logger.debug(f"entry_username={entry_username!r}")

    logger.info('Prompt user for entry password')
    while True:
        try:
            entry_password = entrySession.prompt(message='Password > ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Entry "):
                # True
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new entry password
                pass
        else:
            break

    logger.info('Prompt user for entry url')
    while True:
        try:
            entry_url = entrySession.prompt(message='URL > ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Entry "):
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new entry url
                pass
        else:
            break
    logger.debug(f"entry_url={entry_url!r}")

    logger.info('Prompt user for entry notes')
    while True:
        try:
            entry_notes = entrySession.prompt(message='Notes > ',
            multiline=True,
            show_frame=True,
            bottom_toolbar="Press [Esc] followed by [Enter] to accept input")
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Entry "):
                logger.info("Cancel adding entry by user")
                return (False,"Adding entry cancelled by user")
            else: # Back to prompt for new entry Notes
                pass
        else:
            break
    logger.debug(f"entry_notes={entry_notes!r}")


    # Create entry object
    theEntry = kp.add_entry(entry_group,entry_title,entry_username,entry_password,entry_url,entry_notes)
    logger.debug(f"entry in memory: uuid={theEntry.uuid}, theEntry={theEntry}")

    displayEntry(theEntry)
    # Confirm with user they want to save Entry
    if _confirm("Save Entry "):
        # Saving to the entry
        _saveEntry(theEntry)
        return(True,theEntry)

    kp.delete_entry(theEntry)
    logger.info("Default adding entry cancelled")
    return (False,"Cancel adding entry")

def addGroup() -> tuple:
    """Prompts user for values for various fields for a Group entry

    Returns:
        tuple: (status,msg)
            status (bool):
                True - Group saved in db, msg will be Group obj
                False - Group not saved in db. msg will be why
            msg (any):
                Why not saved, or Group object
    """
    logger.debug("Adding a new group")
    print("Adding a new group")
    addGrpSession = PromptSession()

    logger.info("Prompt user for new Group name")
    while True:
        try:
            grp_name = addGrpSession.prompt(message='Name > ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Group "):
                logger.info("Cancel adding group by user")
                return (False,"Adding group cancelled by user")
            else: # Back to prompt for new group name
                pass
        else:
            break
    logger.info(f"Group Name={grp_name!r}")

    logger.info("Prompt user for parent group")
    while True:
        try:
            # Have user choose, default choice is the current group they are in
            parentGrp = groupChoices(grpUUID=GBLSettings['currentGrp'].uuid)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Group "):
                logger.info("Cancel adding group by user")
                return (False,"Adding group cancelled by user")
            else: # Back to prompt for new group's parent group
                pass
        else:
            break
    logger.info(f"Parent Group uuid:{parentGrp.uuid} title:{parentGrp.name}")

    logger.info('Prompt user for Group notes')
    while True:
        try:
            grp_notes = addGrpSession.prompt(message='Notes > ',
            multiline=True,
            show_frame=True,
            bottom_toolbar="Press [Esc] followed by [Enter] to accept input")

        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Adding Group "):
                logger.info("Cancel adding group by user")
                return (False,"Adding group cancelled by user")
            else: # Back to prompt for new group Notes
                pass
        else:
            break
    logger.info("User entered group notes")
    logger.debug(f"Group Notes={grp_notes!r}")

    # Create group object
    tmpGroup = kp.add_group(parentGrp,group_name=grp_name,notes=grp_notes)
    logger.debug(f"Group created in memory: uuid={tmpGroup.uuid}, object:{tmpGroup}")
    displayGroup(tmpGroup)

    # Prompt User if they want to save group
    logger.info("Prompting user if they want to save")
    if _confirm("Save Group "):
        # Save Group
        logger.info("Confirmed to save Group")
        _saveGroup(tmpGroup)
        return(True,tmpGroup)
    else:
        # Default is not saving group
        logger.info("Adding group cancelled")
        kp.delete_group(tmpGroup)
        return (False, "Adding group cancelled")

def chgDbPass() -> tuple:
    """Change database password
    Returns:
        tuple: (status,msg)
            status (bool):
                True - db password changed
                False - db password not changed
            msg (any):
                message detail for the status
    """
    tmpSession=PromptSession()
    # Prompt user for current password
    logger.info("prompt user for current db password")
    while True:
        try:
            xtmp = tmpSession.prompt("Enter current db password: ", is_password=True)
        except KeyboardInterrupt:
            logger.info("Keyboard Interrupt. Prompt user for current db password")
            logger.info("Cancel changing db password")
            return(False,"Cancel changing db password")
        else:
            break
    # is password the current
    if xtmp != kp.password:
        logger.info("Current password entered did not match")
        return(False,"Password does not match current database password")

    # Get new db password from user
    logger.info("prompt user for new db password")
    while True:
        try:
            newpwd = tmpSession.prompt("Enter NEW db password: ", is_password=True)
        except KeyboardInterrupt:
            logger.info("Keyboard Interrupt. Prompt user for new db password")
            logger.info("Cancel changing db password")
            return(False,"Cancel changing db password")
        else:
            break

    # Make sure new password is not blank
    if newpwd == "":
        logger.info("New password invalid")
        return(False,"New database password invalid")

    # Get confirmation for change
    logger.info("Final prompt to change database password")
    if _confirm("Change the database password "):
        logger.info("Saving new database password")
        try:
            kp.password = newpwd
            kp.save()
            logger.info("Database password changed")
            return(True,"Successfully changed database password")
        except Exception as oopsError:
            logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
            print(f"CRITICAL: Unexpected error {oopsError}")
            traceback.print_exc()
            quit(1)
    else:
        return(False,"Database password change canceled")

    return(False,"Database password not changed")

def helpAction(cmd=None) -> None:
    """Display help info for the command

    Args:
        cmd (str): Default None. command looking for help on. Should be just one word
    """
    logger.info(f"Displaying help for command: {cmd}")
    print("=" * 80)
    if cmd is None:
        print("Commands are:")
        print(f'{list(cmdHelper.keys())}')
        return

    match cmd.lower():
        case 'add':
            print("add: is use to add an entry or group to the database")
            print("Usage: add [ entry | group ]")
            print("  Example: To add an entry to the database")
            print("    add entry")
            print(" Note, the default group/path for the entry is the current location")
        case 'delete' | 'del':
            pass
            print("delete: is used to delete an entry or group")
            print("Usage: delete [ entry | group ] [<uuid>]")
            print(" uuid : optional. the UUID for the entry or group")
            print(" If the uuid is not provided a list is presented to chose from.")
            print("  The list of entries will be for those in the current location.")
            print(" Example: To delete a group with uuid of aabbcde-aaaa-bbb")
            print("  delete group aabbcde-aaaa-bbb")
        case 'edit':
            print("edit: is used to edit an entry or group")
            print("Usage: edit [ entry | group ] [<uuid>]")
            print(" uuid : optional. the UUID for the entry or group")
            print(" If the uuid is not provided a list is presented to chose from.")
            print("  The list of entries will be for those in the current location.")
            print(" Example: To edit entry with uuid of 1234-aaa-bbb")
            print("  edit entry 1234-aaa-bbb")
        case 'find':
            print("find: Used to find entries in the database")
            print("Usage: find ['title' | 'username'] <string to find>")
            print(" Example: To find all entries with Strongmail UI in the title")
            print("   find entry Strongmail UI")
            print("   Will find all records where the title field contains `Strongmail UI` case insensitve")
            print("Results will be displayed on the console")
        case 'chgpwd':
            print("chgpwd: Used to change the database password ")
            print("A prompt for current password is shown so password can be changed")
        case 'chggrp' | 'cd':
            print("chgrp: is used to change the current group/path")
            print("A list of groups/paths will be shown to choose from")
        case 'getpass':
            print("getpass: used to display the password of an entry")
            print("Usage: getpass <uuid>")
            print("Result will be the password displayed for the entry to the console")
        case 'list' | 'ls':
            print("list: Display entries in current group/path")
            print("Usage: list")
            print("       ls")
        case 'show':
            print("show: Used to display details about a specific entry, or group")
            print("Usage: show [ entry | group ] [<uuid>]")
            print(" uuid : optional. the UUID for the entry or group")
            print(" If the uuid is not provided a list is presented to chose from.")
            print("  The list of entries will be for those in the current location.")
            print(" Example: To show the details for the entry with uuid of 1234-aaa-bbb")
            print("  list entry 1234-aaa-bbb")
        case 'quit' | 'exit':
            print("Exit application")
        case _: # Catchall
            print(f"No help found for {cmd}")
    return

def displayGroup(grp) -> None:
    """Display list of entries for a group

    Args:
        grp (PyKeePass.Group): Group object to display the detail for

    """
    displayGroupHeader(grp)
    displayEntriesTable(grp.entries)

def displayGroupHeader(grp) -> None:
    """Display group details

    Args:
        grp (PyKeePass.Group): Group object to display the detail for
    """
    if grp is None:
        logger.info("No group object provided to display")
        print_formatted_text(FormattedText([
            ('class:red','Unable to find Group'),
            ]),style=mainStyles)
        return

    logger.info(f"Displaying group header info for group uuid: {grp.uuid} group name: {grp.name!r}")
    print("=" * 93)
    print_formatted_text(FormattedText([
        ('class:fldname','Group: '),('',f'{grp.name}    '),
        ('class:fldname','UUID: '),('',f'{grp.uuid}\n'),
        ('class:fldname',' Path: '),('',f'{_prettyPath(grp.path)}\n'),
        ('class:fldname', 'Modified: '),('',f'{grp.mtime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}'),
        ('class:fldname', ' Created: '),('',f'{grp.ctime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}\n'),
        ('class:fldname',' Entries: '),('',f'{len(grp.entries)}'),
        ('class:fldname',' Subgroups: '),('',f'{len(grp.subgroups)}\n'),
        ('class:fldname',' Notes:\n'),
        ('',f'{_noNone(grp.notes)}'),
    ]),style=mainStyles)
    print("=" * 93)
    logger.debug(f'Group Name: {grp.name!r}')
    logger.debug(f'Group uuid: {grp.uuid}')
    logger.debug(f'Group path: {grp.path}')
    logger.debug(f'mtime: {grp.mtime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}')
    logger.debug(f'ctime: {grp.ctime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}')
    logger.debug(f'Notes: {grp.notes!r}')
    return

def displayEntriesTable(entries:list) -> None:
    """Display a list of entries

    Args:
        entries (list): list of Entry classes
    """
    logger.info(f"Displaying {len(entries)} entries")
    if entries is None:
        print(' -- No entries found --')
        return
    if len(entries) == 0:
        print(' -- No entries found --')
        return
    # Header
    uuid = " UUID"[0:36].ljust(36)
    title = "Title"[0:50].ljust(50)
    divLine = "-" * 93
    print(divLine)
    print_formatted_text(f"{uuid} | {title} |")
    print(divLine)
    # Details
    for rec in entries:
        uuid = f"{rec.uuid}"[0:36].ljust(36)
        title = f"{rec.title}"[0:50].ljust(50)
        print_formatted_text(f"{uuid} | {title} |")

    print(divLine)
    return

def displayEntry(entry) -> None:
    """Display an entry on the console

    Args:
        entry (PyKeePass.Entry): Entry object that is being displayed
    """
    logger.debug(f"displaying Entry: {entry}")
    if _noNone(entry.password) == "" :
        dplayPass = '-- Nothing set --'
    else:
        dplayPass = '-----------------'

    print("=" * 93)
    print_formatted_text(FormattedText([
        ('class:fldname','   Entry: '),('',f'{_noNone(entry.title)} '),
        ('class:fldname','    UUID: '),('',f'{entry.uuid}\n'),
        ('class:fldname','    Path: '),('',f'{_prettyPath(entry.path)}\n'),
        ('class:fldname','    User: '),('',f'{_noNone(entry.username)}\n'),
        ('class:fldname','Password: '),('',f'{dplayPass}\n'),
        ('class:fldname','     URL: '),('',f'{_noNone(entry.url)}'),
    ]),style=mainStyles)

    print_formatted_text(FormattedText([
        ('class:fldname', 'Modified: '),('',f'{entry.mtime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}'),
        ('class:fldname', ' Created: '),('',f'{entry.ctime.astimezone().strftime('%Y-%m-%d %I:%M:%S %p')}'),
    ]),style=mainStyles)

    print_formatted_text(FormattedText([
        ('class:fldname', 'Notes: '),
    ]),style=mainStyles)
    print(_noNone(entry.notes))
    print("-" * 93)
    return

def delAction(cmdOptions:str) -> None:
    """Delete command validation
    This will delete an entry or a group

    Args:
        cmdOptions (str): Entry or Group and it's uuid to be deleted. uuid is optional
          Example: entry <uuid>
          Would edit the entry with the specific uuid
    """
    logger.debug("Parsing command")
    # Make sure a blank string was not passed
    if _noNone(cmdOptions) == "": # can't process
        print("Invalid/Incomplete delete command")
        helpAction('delete')
        return

    # Strip whitespace
    xtmp = cmdOptions.strip()
    # Split into parts
    cmdParts = xtmp.split(' ')
    logger.debug(f"cmdParts = {cmdParts}")

    # Determine if entry or group is being deleted
    match cmdParts[0].lower():
        case 'entry':
            logger.debug("Delete an entry has been requested")
            if len(cmdParts) > 1: # Last part could be the uuid
                # Confirm valid uuid
                logger.debug(f"Determine if {cmdParts[1]} is a valid UUID")
                try:
                    entryUUID = uuid.UUID(cmdParts[1])
                except ValueError:
                    print_formatted_text(FormattedText([
                        ('class:red','Invalid UUID'),
                    ]),style=mainStyles)
                    return
                except Exception as oopsError:
                    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                    print(f"CRITICAL: Unexpected error {oopsError}")
                    traceback.print_exc()
                    quit(1)
            else: # Have user chose an entry to get a UUID
                logger.debug("Prompting user for entry to delete")
                # Are there entries for use to chose from
                tmpChoices = entryChoices(GBLSettings['currentGrp'])
                if len(tmpChoices) == 0: # No entries in group
                    print(f"No entries to edit for current group {GBLSettings['currentGrp']}")
                    return
                else: # Have user chose an entry
                    entryUUID = choice(
                        message=f"Select an Entry for group {_prettyPath(GBLSettings['currentGrp'].path)} to delete",
                        options=tmpChoices,
                        bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept.")
                        )
                    print(f" >> delete entry {entryUUID}")

            # Got a valid entry uuid. Find and edit it.
            logger.info(f"Searching for entry uuid {entryUUID}")
            theEntry = kp.find_entries(uuid=entryUUID,first=True)
            if theEntry is None: # Entry not found.. Nothing to do
                logger.info(f"entry uuid {entryUUID} was not found")
                print_formatted_text(FormattedText([
                    ('class:red','Unable to find entry for uuid'),
                ]),style=mainStyles)
                return

            # Proceed with the delete entry logic
            displayEntry(theEntry)
            logger.info(f"Delete entry uuid={theEntry.uuid}, title={theEntry.title!r}")
            success,msg = delEntry(theEntry)
            if success: # Entry successfully edited
                logger.info(f"Entry uuid={theEntry.uuid}, {msg}")
                print_formatted_text(FormattedText([('class:green',f'{msg}')]),style=mainStyles)
            else: # Entry was not saved
                logger.info(f"Entry uuid={theEntry.uuid} was not deleted/recycled. {msg}")
                print_formatted_text(FormattedText([('class:red',f'{msg}')]),style=mainStyles)
        case 'group':
            #TODO: deleting an Group
            print("TODO: Delete a Group not ready")
            return
    return

def delEntry(theEntry) -> tuple:
    """Delete or Recycle an Entry in db

    Will prompt user accordingly if the want delete/recycle or cancel the entry deletion.
    If the entry is in the recycle bin, then user would be delete or cancel.

    Args:
        theEntry (PyKeePass.Entry): The Entry object that is being delete

    Returns:
        tuple:
            status (bool):
                True: Entry was deleted/recycled
                False: Entry was not deleted/recycled
            str:
                Message to what happend. Example 'Entry permanently deleted'
    """
    #Determine if theEntry is in the Recycle Group
    if _isEntryInRecycle(theEntry):
        # Ask user if they want to Delete (no recovery) or cancel delete
        while True:
            try:
                logger.debug("Prompt user to perm delete, or Cancel")
                usrOptions=[
                    (1,'Permanently delete Entry'),
                    (2,'Cancel deleting Entry'),
                ]
                usrChoice = choice(
                    message="Options for deleting Entry",
                    options=usrOptions,
                    default=2,
                    bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept.")
                    )
            except KeyboardInterrupt:
                logger.debug("Keyboard Interrupt. Prompt user to delete (no recovery) or cancel")
                return (False,"Deleting Entry canceled")
            else: # Back to prompt for user to delete or cancel
                break
    else: # Not in the recycle bin
        # Ask user if they want to Recycle, Delete (no recovery), cancel delete
        while True:
            try:
                logger.debug("Prompt user to Recycle, perm delete, or Cancel")
                usrOptions=[
                    (0,f"Put Entry in Recycle Bin {kp.recyclebin_group}"),
                    (1,'Permanently delete Entry'),
                    (2,'Cancel deleting Entry'),
                ]
                usrChoice = choice(
                    message="Options for deleting Entry",
                    options=usrOptions,
                    default=2,
                    bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept.")
                    )
            except KeyboardInterrupt:
                logger.debug("Keyboard Interrupt. Prompt user to delete (no recovery) or cancel")
                return (False,"Deleting Entry canceled")
            else: # Back to prompt for user to delete or cancel
                break

    logger.debug(f"User chose: {usrChoice}")
    match usrChoice:
        case 0: # Put entry into Recycle Bin
            logger.info(f"Entry uuid: {theEntry.uuid} being put into database recycle bin")
            kp.trash_entry(theEntry)
            _saveEntry(theEntry)
            return (True,f'Entry in database recycle bin {kp.recyclebin_group}')
        case 1: # Permanently Delete Entry
            logger.info(f"Entry uuid: {theEntry.uuid} being permanently deleted. {theEntry}")
            kp.delete_entry(theEntry)
            kp.save() # Not doing the _saveEntry as that method will touch the delete entry and cause problems
            return (True,'Entry permanently deleted')

    return (False,'Delete entry canceled')

def editAction(editOptions:str) -> None:
    """Edit command validation
    This will edit an entry or a group

    Args:
        editOptions (str): Entry or Group and it's uuid to be edited.
          Example: entry <uuid>
          Would edit the entry with the specific uuid
    """
    logger.debug("Parsing edit command")
    # Was valid info options provided?
    if _noNone(editOptions) == "": # can't process
        print("Invalid/Incomplete edit command")
        helpAction('edit')
        return

    # Strip whitespace
    xtmp = editOptions.strip()
    # Split into parts
    editParts = xtmp.split(' ')
    logger.debug(f"editParts = {editParts}")

    # Determine if entry or group is being edited
    match editParts[0].lower():
        case 'entry':
            logger.debug("Edit an entry has been requested")
            # Is there a entry UUID for the entry
            if len(editParts) > 1: # Last part could be the uuid
                # Confirm valid uuid
                logger.debug(f"Determine if {editParts[1]} is a valid UUID")
                try:
                    entryUUID = uuid.UUID(editParts[1])
                except ValueError:
                    print_formatted_text(FormattedText([
                        ('class:red','Invalid UUID'),
                    ]),style=mainStyles)
                    return
                except Exception as oopsError:
                    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                    print(f"CRITICAL: Unexpected error {oopsError}")
                    traceback.print_exc()
                    quit(1)
            else: # Have user chose an entry so we'll have a UUID
                logger.info("Prompting user for an entry to edit")
                # Are there entries for use to chose from
                tmpChoices = entryChoices(GBLSettings['currentGrp'])
                if len(tmpChoices) == 0: # No entries in group
                    logger.info("No entries found in current group {GBLSettings['currentGrp']}")
                    print(f"No entries to edit for current group {GBLSettings['currentGrp']}")
                    return
                else: # Have user chose an entry
                    while True:
                        try:
                            entryUUID = choice(
                                message=f"Select an Entry from group {_prettyPath(GBLSettings['currentGrp'].path)}",
                                options=tmpChoices,
                                bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept.")
                                )
                        except KeyboardInterrupt:
                            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
                            if _confirm("Cancel Edit Entry "):
                                logger.info("Cancel edit entry by user")
                                return (False,"Editing entry cancelled by user")
                            else: # Back to user prompt for entry
                                pass
                        else:
                            break

                    print(f" >> edit entry {entryUUID}")

            # Got a valid entry uuid. Find and edit it.
            logger.info(f"Searching for entry uuid {entryUUID}")
            theEntry = kp.find_entries(uuid=entryUUID,first=True)
            if theEntry is None: # Entry not found.. Nothing to do
                logger.info(f"entry uuid {entryUUID} was not found")
                print_formatted_text(FormattedText([
                    ('class:red','Unable to find entry for uuid'),
                ]),style=mainStyles)
                return

            # Go forth and edit the Entry
            displayEntry(theEntry)
            logger.info(f"Going to edit entry uuid={theEntry.uuid}, title={theEntry.title!r}")
            success,msg = editEntry(theEntry)
            if success: # Entry successfully edited
                logger.info(f"Entry uuid={msg.uuid} edit completed")
                displayEntry(msg)
            else: # Entry was not saved
                logger.info(f"Entry uuid={theEntry.uuid} was not edited. {msg}")
                print_formatted_text(FormattedText([('class:red',f'{msg}')]),style=mainStyles)
        case 'group':
            logger.debug("Edit a group has been requested")
            # Is there a group UUID for the entry
            if len(editParts) > 1: # Last part could be the uuid
                theGroup = None
                # Confirm valid uuid
                logger.debug(f"Determine if {editParts[1]} is a valid UUID")
                try:
                    uniqueID = uuid.UUID(editParts[1])
                except ValueError:
                    print_formatted_text(FormattedText([
                        ('class:red','Invalid UUID'),
                    ]),style=mainStyles)
                    return
                except Exception as oopsError:
                    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                    print(f"CRITICAL: Unexpected error {oopsError}")
                    traceback.print_exc()
                    quit(1)
            else: # No uuid get user to choose a group
                logger.info("Prompting user for group to edit")
                while True:
                    try:
                        theGroup = groupChoices(grpUUID=GBLSettings['currentGrp'].uuid)
                    except KeyboardInterrupt:
                        logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
                        if _confirm("Cancel Edit Group "):
                            logger.info("Cancel edit group by user")
                            return (False,"Editing group cancelled by user")
                        else: # Back to user prompt for group
                            pass
                    else:
                        break
                print(f" >> edit group {theGroup.uuid}")

            if theGroup is None: # User provided a uniqueID so go find it
                theGroup = kp.find_groups(uuid=uniqueID,first=True)
                if theGroup is None:
                    logger.info(f"Group uuid {uniqueID} was not found")
                    print_formatted_text(FormattedText([
                        ('class:red','Unable to find Group uuid'),
                    ]),style=mainStyles)
                    return

            # Go and edit the group
            displayGroupHeader(theGroup)
            logger.info(f"Going to edit group UUID: {theGroup.uuid}, name={theGroup.name!r}")
            success,msg = editGroup(theGroup)
            if success: # Group successfully edited and saved
                logger.info(f"Group UUID: {msg.uuid} edit completed, and group saved")
                displayGroupHeader(msg)
            else: # Group was not successfully edited
                logger.info(f"Group uuid={theGroup.uuid} was not edited. {msg}")
                print_formatted_text(FormattedText([('class:red',f'{msg}')]),style=mainStyles)
            return
        case _: # Catch all
            print("Invalid/Incomplete edit command")
            helpAction('edit')

    return

def editEntry(theEntry) -> tuple:
    """Entry edit prompts user interacts with

    Args:
        theEntry (PyKeePass.Entry): The Entry object that is being edited

    Returns:
        tuple:
            status (bool):
                True: Entry edited and saved. Entry is in the next element.
            Entry | str:
                If status True, the Entry, else string of why edit was not successful
    """
    logger.debug(f"Editing Entry uuid: {theEntry.uuid}")
    entrySession = PromptSession()

    # Edit title
    logger.info(f'Editing Entry uuid: {theEntry.uuid}, Prompt user for entry title')
    # Convert None to a blank string
    editText = _noNone(theEntry.title)
    promptText = [
        ('class:promptfield','Title >'),
        ('','  '),
    ]
    while True:
        try:
            entry_title = entrySession.prompt(message=promptText,style=mainStyles,default=editText)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Entry "):
                # Cancel editing entry
                logger.info("Edit Entry cancelled")
                return (False,"Edit Entry cancelled")
            else: # Back to editing the Entry title
                pass
        else:
            break

    logger.info(f"Editing Entry uuid: {theEntry.uuid}, entry_title={entry_title!r}")

    # Edit group/path
    logger.info('Prompt user for entry group/path')
    # Current Group path for the entry
    tmpGrpPath = theEntry.path.copy()
    # pop the last entry which is the Entry
    tmpGrpPath.pop()
    logger.info(f'Getting group UUID for the entry uuid:{theEntry.uuid}, path:{tmpGrpPath}')
    entryGrp = kp.find_groups(path=tmpGrpPath,first=True)
    if entryGrp is None:
        logger.critical(f'The group should have been found for entry: {theEntry.uuid}')
        quit(1)
    logger.info(f"entry uuid:{theEntry.uuid} group uuid: {entryGrp.uuid}")
    while True:
        try:
            logger.debug(f"Entry uuid:{theEntry.uuid} currently in group uuid:{entryGrp.uuid}")
            selGroup = groupChoices(grpUUID=entryGrp.uuid)
            logger.debug(f"User choose group uuid: {selGroup.uuid}, original group uuid: {entryGrp.uuid}")
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Entry "):
                # Cancel editing entry
                logger.info("Edit Entry cancelled")
                return (False,"Edit Entry cancelled")
            else: # Back to editing the Entry username
                pass
        else:
            break

    # Edit username
    logger.info(f'Editing Entry uuid: {theEntry.uuid}, Prompt user for entry username')
    # Convert None to a blank string
    editText = _noNone(theEntry.username)
    promptText = [
        ('class:promptfield','Username >'),
        ('','  '),
    ]
    while True:
        try:
            entry_username = entrySession.prompt(message=promptText,style=mainStyles,default=editText)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Entry "):
                # Cancel editing entry
                logger.info("Edit Entry cancelled")
                return (False,"Edit Entry cancelled")
            else: # Back to editing the Entry username
                pass
        else:
            break

    logger.info(f"Editing Entry uuid: {theEntry.uuid}, entry_username={entry_username!r}")

    # Edit password
    logger.info(f'Editing Entry uuid: {theEntry.uuid}, Prompt user for entry password')
    # Convert None to a blank string
    editText = _noNone(theEntry.password)
    promptText = [
        ('class:promptfield','Password >'),
        ('','  '),
    ]
    while True:
        try:
            entry_password = entrySession.prompt(message=promptText,style=mainStyles,default=editText)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Entry "):
                # Cancel editing entry
                logger.info("Edit Entry cancelled")
                return (False,"Edit Entry cancelled")
            else: # Back to editing the Entry password
                pass
        else:
            break

    # Edit url
    logger.info(f'Editing Entry uuid: {theEntry.uuid}, Prompt user for entry url')
    # Convert None to a blank string
    editText = _noNone(theEntry.url)
    promptText = [
        ('class:promptfield','Url >'),
        ('','  '),
    ]
    while True:
        try:
            entry_url = entrySession.prompt(message=promptText,style=mainStyles,default=editText)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Entry "):
                # Cancel editing entry
                logger.info("Edit Entry cancelled")
                return (False,"Edit Entry cancelled")
            else: # Back to editing the Entry url
                pass
        else:
            break

    logger.info(f"Editing Entry uuid: {theEntry.uuid}, entry_url={entry_url!r}")

    # Prompt user if they want to edit the entry notes
    edtNotes = False
    if _confirm("Edit entry notes "):
        edtNotes = True
        # Edit Notes
        logger.info(f'Editing Entry uuid: {theEntry.uuid}, Prompt user for entry Notes')
        # Convert None to a blank string
        editText = _noNone(theEntry.notes)
        promptText = [
            ('class:promptfield','Notes >'),
            ('','  '),
        ]
        while True:
            try:
                entry_notes = entrySession.prompt(message=promptText,style=mainStyles,
                default=editText,
                multiline=True,
                show_frame=True,
                bottom_toolbar="Press [Esc] followed by [Enter] to accept input")
            except KeyboardInterrupt:
                logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
                if _confirm("Cancel Editing Entry "):
                    # Cancel editing entry
                    logger.info("Edit Entry cancelled")
                    return (False,"Edit Entry cancelled")
                else: # Back to prompt for entry Notes
                    pass
            else:
                break

        logger.debug(f"Editing Entry uuid: {theEntry.uuid}, entry_notes={entry_notes!r}")

    # Confirm with user to save the Entry
    if _confirm("Save Entry "):
        # Saving to the entry
        theEntry.title = entry_title
        theEntry.username = entry_username
        theEntry.password = entry_password
        theEntry.entry_url = entry_url
        if edtNotes:
            theEntry.notes = entry_notes
        if entryGrp.uuid != selGroup.uuid: # Group changed
            # Moving Entry to another group
            logger.info(f"Editing Entry uuid: {theEntry.uuid} moving from group UUID: {entryGrp.uuid} to group UUID: {selGroup.uuid}")
            kp.move_entry(theEntry,selGroup)
        _saveEntry(theEntry)
        return(True,theEntry)
    else: # Cancel adding entry
        logger.info("Cancel edit entry")
        return (False,"Cancel edit entry")

def editGroup(theGroup) -> tuple:
    """Edit the group

    Args:
        theGroup (PyKeePass.Group): Group object to be edited

    Returns:
        tuple: Result of editing the group
            status (bool):
                True: Group edited and saved. Group is in the next element.
            Entry | str:
                If status True, the Group, else string of why edit was not successful
    """
    logger.debug(f"Editing Group uuid: {theGroup.uuid}")
    groupEditSession = PromptSession()

    # Edit group Name
    logger.info(f'Editing Group uuid: {theGroup.uuid}, Prompt user for group name')
    editText = _noNone(theGroup.name)
    promptText = [
        ('class:promptfield','Name >'),
        ('','  '),
    ]
    while True:
        try:
            grp_name = groupEditSession.prompt(message=promptText,style=mainStyles,default=editText)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
            if _confirm("Cancel Editing Group "):
                # Cancel editing the group
                logger.info("Cancel editing group")
                return (False,"Edit Group cancelled")
            else: # Back to editing the Group title
                pass
        else:
            break

    logger.info(f"Editing Group uuid: {theGroup.uuid}, Group name: {grp_name!r}")

    # Prompt user if they want to edit group notes
    edtNotes = False
    if _confirm("Edit group notes "):
        # Edit group Notes
        edtNotes = True

        logger.info(f'Editing Group uuid: {theGroup.uuid}, Prompt user for group Notes')
        editText = _noNone(theGroup.notes)
        promptText = [
            ('class:promptfield','Notes >'),
            ('','  '),
        ]
        while True:
            try:
                grp_notes = groupEditSession.prompt(message=promptText,style=mainStyles,
                default=editText,
                multiline=True,
                show_frame=True,
                bottom_toolbar="Press [Esc] followed by [Enter] to accept input")
            except KeyboardInterrupt:
                logger.debug("Keyboard Interrupt. Prompt user if they want to continue")
                if _confirm("Cancel Editing Group "):
                    # Cancel editing the group
                    logger.info("Cancel editing group")
                    return (False,"Edit Group cancelled")
                else: # Back to prompt for group Notes
                    pass
            else:
                break
        logger.info(f"Editing Group uuid: {theGroup.uuid}, grp_notes={grp_notes!r}")

    # Confirm with user to save Group
    logger.info(f"Editing Group uuid: {theGroup.uuid}, Prompt user if the want to save group")
    if _confirm("Save Group "):
        # Save Group
        theGroup.name = grp_name
        if edtNotes:
            theGroup.notes = grp_notes
        _saveGroup(theGroup)
        return(True,theGroup)
    else: # Cancel Saving Group
        logger.info("Cancel save edited group")
        return (False,"Cancelled saving the group")

def entryChoices(grp) -> tuple:
    """Create a tuple of all the entries which exist in the grp

    Args:
        grp (PyKeePass.Group): Group object to get a list of entries

    Returns:
        tuple: Each row containing the entry.uuid, and entry.title
    """
    logger.debug(f"Creating entry list for group UUID: {grp.uuid}. Entries: {len(grp.entries)}")
    tmpList = []
    for entry in grp.entries:
        entryRow = [entry.uuid,entry.title]
        logger.debug(f"Appending entry.uuid={entry.uuid}, entry.title={entry.title}")
        tmpList.append(entryRow)

    logger.debug(f"entry list records: {len(tmpList)}")
    return tuple(tmpList)

def findAction(findOptions:str) -> None:
    """Find entry/s which meet the critera in args and display on screen

    Args:
        args (str): What to find by and the values.
            Format: key srcString
        Example: title My test entry
         Searchs titles for the string "My test entry" case insensitive
    Returns:
        None. Just display resutls or issues on console
    """
    if findOptions is None: # can't process
        print("Incomplete find command")
        return
    if findOptions == "": # can't process
        print("Incomplete find command")
        return
    xtmp = findOptions.strip()
    if xtmp.find(' ') != -1:
        srchStr = xtmp.split(' ',1)[1].strip()
    else: # Incomplete find command
        print("Incomplete find command")
        return

    # What field are we searching
    srchBy = xtmp.split(' ',1)[0]
    logger.debug(f"searching by {srchBy}")
    match srchBy.lower():
        case 'title':
            logger.info(f"searching 'title' for : {srchStr}")
            results = kp.find_entries(title=srchStr,regex=True,flags="i")
        case 'username':
            logger.info(f"searching 'username' for : {srchStr}")
            results = kp.find_entries(username=srchStr,regex=True,flags="i")
        case _: # Catch all
            print("Incomplete find command")
            return

    print(f"Found {len(results)} records")
    logger.info(f"Found {len(results)} records")
    displayEntriesTable(results)
    return

def groupChoices(grpUUID=None):
    """Prompt for user to choose a group

    Keepass allows non unique group names. Thus displaying to the user the
    group PATHS for user to choose

    Args:
        grpUUID: Default group UUID picked for user. Default is None
    Returns:
        PyKeePass.Group object
    """
    tmpList = []
    logger.info(f"Creating list of groups for user to choose from. Default UUID is: {grpUUID}")
    for grp in kp.groups:
        uiEntry = _prettyPath(grp.path)
        grpRow = [grp.uuid,uiEntry]
        logger.debug(f"group_name={grp.name}, group_uuid={grp.uuid}, uiEntry={uiEntry}")
        tmpList.append(grpRow)

    logger.info(f"Displaying {len(tmpList)} groups for user to choose from")
    tmpGrp = choice(message="Select a Group path",
        options=tmpList,
        bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept."),
        show_frame=~is_done,
        default=grpUUID)
    logger.info(f"User picked {tmpGrp}")
    logger.info("Getting group object and returning")
    return kp.find_groups(uuid=tmpGrp,first=True)

def changeGrp() -> None:
    """Change the current group/path

    Sets the global settings for the current path when
    user choses which one
    """
    logger.debug("Prompting user for group to change to")
    GBLSettings['currentGrp'] = groupChoices(grpUUID=GBLSettings['currentGrp'].uuid)
    logger.info(f"Setting current group to uuid: {GBLSettings['currentGrp'].uuid}")
    return

def showAction(showOptions:str) -> None:
    """Show validation determines to show entry/group

    Args:
        showOptions (str): 1 or 2 words.
            first: (entry | group) Determines if entry or group is going to be display
            second (optional) : uuid of the the entry or group
            If the second is missing user will be provided choices

    Returns:
        None. Takes appropiate action to display info to console
    """
    logger.info("Parsing show command arguments")
    # Was valid info options provided?
    if _noNone(showOptions) == "": # can't process
        print("Invalid/Incomplete show command")
        helpAction('show')
        return

    # Strip whitespace
    xtmp = showOptions.strip()
    # Split into parts
    showParts = xtmp.split(' ')
    logger.debug(f"showParts = {showParts}")

    # Determine entry/Group to show details
    match showParts[0].lower():
        case 'entry':
            logger.debug("details for an entry requested")
            # Is there a UUID for the entry
            if len(showParts) > 1: # Last part could be the uuid
                # Confirm valid uuid
                logger.debug(f"Determine if {showParts[1]} is a valid UUID")
                try:
                    uniqueID = uuid.UUID(showParts[1])
                except ValueError:
                    print_formatted_text(FormattedText([
                        ('class:red','Invalid UUID'),
                    ]),style=mainStyles)
                    return
                except Exception as oopsError:
                    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                    print(f"CRITICAL: Unexpected error {oopsError}")
                    traceback.print_exc()
                    quit(1)
            else: # Get a UUID from user
                # Are there entries for use to chose from
                tmpChoices = entryChoices(GBLSettings['currentGrp'])
                if len(tmpChoices) == 0: # No entries in group
                    print("No entries to show in group")
                    return
                else: # Have user chose an entry
                    uniqueID = choice(
                        message=f"Select an Entry for group {_prettyPath(GBLSettings['currentGrp'].path)}",
                        options=tmpChoices,
                        bottom_toolbar=HTML(" Press <b>[Up]</b>/<b>[Down]</b> to select, <b>[Enter]</b> to accept.")
                        )
                    print(f" >> show entry {uniqueID}")

            # Got a valid UUID. Find the entry and display
            logger.debug(f"Finding entry where uuid={uniqueID}")
            result = kp.find_entries(uuid=uniqueID,first=True)
            logger.info(f"Results for finding {uniqueID}: {result}")
            if result is None: # Entry not found
                logger.info(f"entry uuid {uniqueID} was not found")
                print_formatted_text(FormattedText([
                    ('class:red','Unable to find entry for uuid'),
                ]),style=mainStyles)
                return

            displayEntry(result)
            return
        case 'group':
            logger.debug("details for a group requested")
            # Is there a group UUID for the entry
            if len(showParts) > 1: # Last part could be the uuid
                theGroup = None
                # Confirm valid uuid
                logger.debug(f"Determine if {showParts[1]} is a valid UUID")
                try:
                    uniqueID = uuid.UUID(showParts[1])
                except ValueError:
                    print_formatted_text(FormattedText([
                        ('class:red','Invalid UUID'),
                    ]),style=mainStyles)
                    return
                except Exception as oopsError:
                    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                    print(f"CRITICAL: Unexpected error {oopsError}")
                    traceback.print_exc()
                    quit(1)
            else: # No uuid get user to choose a group
                logger.debug("Prompting user for group to get details for")
                theGroup = groupChoices(grpUUID=GBLSettings['currentGrp'].uuid)
                print(f" >> show group {theGroup.uuid}")

            if theGroup is None: # User provided group uuid
                logger.debug(f"Getting group entry for uuid={uniqueID}")
                theGroup = kp.find_groups(uuid=uniqueID,first=True)

            displayGroupHeader(grp=theGroup)
        case _: # Catch all
            print("Invalid/Incomplete show command")
            helpAction('show')
            return
    return

def getPass(uniqueID:uuid) -> None:
    """Get password for entry's uuid and display to the console"""
    if uniqueID is None:
        print("Incomplete getpass command")
        helpAction("getpass")
        return
    if uniqueID == "":
        print("Incomplete getpass command")
        helpAction("getpass")
        return

    logger.info(f"getting password for entry {uniqueID}")
    theEntry = kp.find_entries(uuid=uniqueID,first=True)

    if theEntry.password is None:
        print_formatted_text(FormattedText([
            ('class:red','Entry has no password entry'),
        ]),style=mainStyles)

        logger.info("Entry has no password entry")
        return

    # Bug coping to clipboard. BAC has some sneaky things going on, or Windows 11 really sucks.
    # sometimes nothing is copied. Sometimes everything in the cmd prompt is selected and copied.
    print(theEntry.password)
    logger.info("Password retrieved")
    return

def main(args):
    #======== Main loop for the session

    # Set global setting for current group to the root group/path
    GBLSettings['currentGrp'] = kp.find_groups(path='', first=True)

    completer = NestedCompleter.from_nested_dict(cmdHelper)
    session = PromptSession()
    while True:
        try:
            userCmd = session.prompt(
                ' Command > ',
                completer=completer,
                complete_style=CompleteStyle.MULTI_COLUMN,
                reserve_space_for_menu=3,
                bottom_toolbar=_btmBarCurPath)
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt. Exiting Application")
            break
        except EOFError:
            logger.info("EOFError. Exiting application")
            break
        else: # checking for valid command/action
            logger.info(f"Command: {userCmd}")
            try: # User entered a commmand
                action = userCmd.split(' ',1)[0]
            except IndexError: #Why is this here?
                break

            match action:
                case 'cls' | 'clear':
                    cls()
                case 'add':
                    logger.debug(f"Add Command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        cmd_breakdown = userCmd.split(' ')
                        match cmd_breakdown[1].lower():
                            case 'entry':
                                logger.info("Adding an entry")
                                addStatus, addMsg = addEntry()
                                if addStatus: # New entry was saved to database
                                    logger.debug(f"UUID of entry: {addMsg.uuid}. Entry={addMsg}")
                                    displayEntry(addMsg)
                                else: # new entry was not saved to database
                                    logger.debug("Entry was not saved to database")
                                    print_formatted_text(FormattedText([
                                        ('class:red',f'{addMsg}')
                                    ]),style=mainStyles)
                            case 'group':
                                addStatus,addMsg = addGroup()
                                logger.info(f"addResult is: {addStatus, addMsg}")
                                if addStatus: # New group was saved to database
                                    displayGroup(addMsg)
                                else: # New Group was not saved to database
                                    print_formatted_text(FormattedText([
                                        ('class:red',f'{addMsg}')
                                    ]),style=mainStyles)
                            case _: # Catch all
                                print("add command incomplete")
                                helpAction("add")
                    else:
                        print("add command incomplete")
                        helpAction("add")
                case 'chggrp' | 'cd':
                    # Changing current group
                    changeGrp()
                    # Now display group and it's entries
                    displayGroup(GBLSettings['currentGrp'])
                case 'chgpwd':
                    logger.info("Change database password")
                    success,msg = chgDbPass()
                    if success: # password changed
                        print_formatted_text(FormattedText([('class:green','Database password changed')]),style=mainStyles)
                    else: # password not changed
                        print_formatted_text(FormattedText([('class:red',f'{msg}')]),style=mainStyles)
                case 'delete':
                    logger.debug(f"Delete Command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        objCmd = userCmd.split(' ',1)[1] # strip command and keep args
                        delAction(objCmd)
                    else:
                        print("delete command incomplete")
                        helpAction("delete")
                case 'edit':
                    logger.debug(f"Edit Command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        objCmd = userCmd.split(' ',1)[1] # strip command and keep args
                        editAction(objCmd)
                    else:
                        print("edit command incomplete")
                        helpAction("edit")
                case 'find':
                    logger.debug(f"Find command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        objCmd = userCmd.split(' ',1)[1] # strip command and keep args
                        findAction(objCmd)
                    else:
                        print("Incomplete find command")
                        helpAction("find")
                case 'show':
                    logger.debug(f"Show Command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        objCmd = userCmd.split(' ',1)[1] # strip command and keep args
                        showAction(objCmd)
                    else:
                        print("show command incomplete")
                        helpAction("show")
                case 'getpass':
                    logger.debug(f"getpass Command found in: {userCmd}")
                    if userCmd.find(' ') != -1:
                        objCmd = userCmd.split(' ',1)[1]
                        try:
                            uniqueID = uuid.UUID(objCmd.strip())
                            getPass(uniqueID)
                        except ValueError:
                            print_formatted_text(FormattedText([
                                ('class:red','Invalid UUID'),
                            ]),style=mainStyles)
                        except Exception as oopsError:
                            logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
                            print(f"CRITICAL: Unexpected error {oopsError}")
                            traceback.print_exc()
                            quit(1)
                    else:
                        print("getpass command incomplete")
                        helpAction("getpass")
                case 'list' | 'ls':
                    logger.debug("Listing entries in current group")
                    displayGroup(GBLSettings['currentGrp'])
                case 'reload':
                    logger.debug("Reloading database")
                    print("=" * 93)
                    kp.reload()
                    print("Database reloaded")
                case 'help':
                    if userCmd.find(' ') != -1:
                        # Help on what command
                        objCmd = userCmd[userCmd.find(' '):]
                        helpAction(objCmd.strip())
                    else:
                        helpAction(None)
                case 'quit' | 'exit':
                    quit()
                case _: # Catch all
                    print_formatted_text(FormattedText([
                        ('class:red','Unknown command'),
                    ]),style=mainStyles)
    print('GoodBye!')

def _confirm(msg:str) -> bool:
    """Replacement for prompt_toolkit.shortcuts.confirm which raises an exception for control+c

    Args:
        msg (str): Message to provide to user. Suffix will always be '(y/N) ? '
    Returns:
        bool: Default False. ONLY True when user presses 'Y' or 'y'.
    """
    while True:
        try:
            tmpAnswer = confirm(message=msg, suffix='(y/N) ? ')
        except KeyboardInterrupt:
            logger.debug("Keyboard Interrupt in confirmation")
            tmpAnswer = False
            break
        except Exception as oopsError:
            logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
            print(f"CRITICAL: Unexpected error {oopsError}")
            traceback.print_exc()
            quit(1)
        else:
            break

    if tmpAnswer:
        return True
    else:
        return False

def _grpEntries(grp) -> None:
    """Recursively goes though group (grp) and displays to console

    Args:
        grp (PyKeePass.Group): Group object to get listed
    """
    displayGroup(grp)
    for subGrp in grp.subgroups:
        _grpEntries(subGrp)

def _isEntryInRecycle(theEntry) -> bool:
    """Checks if theEntry is in the database Recycle bin

    Database Recycle bin can have any name so this accounts
    for that.

    Args:
        theEntry (pyKeePass.Entry): The entry object that is being checked

    Returns:
        bool: if the entry is in the database's recycle bin
            True: theEntry is in the recycle bin
            False: theEntry is not in the recycle bin
    """
    # Get db's recycle group
    logger.debug("Getting recycle bin group")
    recycleGrp = kp.recyclebin_group
    # Get entryies path (poping last as that's the entry itself)
    tmpEpath = theEntry.path.copy()
    tmpEpath.pop() # pop out the Entry from the path
    logger.debug(f"tmpEpath={tmpEpath}, recycleGrp.path={recycleGrp.path}")
    if tmpEpath == recycleGrp.path: # Entry is in the recycle bin
        logger.debug(f"Entry uuid: {theEntry.uuid} is in database recycle bin: {recycleGrp.path}")
        return True
    else:
        logger.debug(f"Entry uuid: {theEntry.uuid} is NOT in database recycle bin: {recycleGrp.path}")
        return False

def _prettyPath(pathList:list) -> str:
    """Take the elements in a list and make it pretty

    Example: ["level 1", "level 2", "Level/this/thing", "and here"]
     Returns: "level 1 > level 2 > Level/this/thing, and here"
    """

    if len(pathList) == 0:
        xString = "Root"
    else:
        xString = pathList[0]
        for index,value in enumerate(pathList):
            if index == 0:
                pass
            else:
                xString = xString + f" > {value}"
    return xString

def _saveGroup(grp) -> None:
    """Update modify date for a group and save to db

    Args:
        grp (PyKeePass.Group): Group object to be saved
    """
    try:
        grp.touch(modify=True)
        logger.debug(f"Saving Group uuid: {grp.uuid}")
        kp.save()
        logger.info(f"{grp} uuid: {grp.uuid} has been saved")
        print_formatted_text(FormattedText([('class:green','Group saved')]),style=mainStyles)
    except Exception as oopsError:
        logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
        print(f"CRITICAL: Unexpected error {oopsError}")
        traceback.print_exc()
        quit(1)
    return

def _saveEntry(entry) -> None:
    """Update modify date for the entry, and will save to db"""
    try:
        entry.touch(modify=True)
        logger.debug(f"saving entry {entry.uuid}")
        kp.save()
        logger.info(f"Saved entry {entry.uuid}")
        print_formatted_text(FormattedText([('class:green','Entry saved')]),style=mainStyles)
    except Exception as oopsError:
        logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
        print(f"CRITICAL: Unexpected error {oopsError}")
        traceback.print_exc()
        quit(1)
    return

def _noNone(theVal) -> str:
    """Returns blank string if theVal is None else theVal"""
    if theVal is None:
        return ""
    else:
        return theVal

def _btmBarCurPath() -> str:
    """Returns a friendly string of the current path for the bottom bar"""
    return f"Group Name: {GBLSettings['currentGrp'].name} | path: {_prettyPath(GBLSettings['currentGrp'].path)}"

# ==============================
# Getting the basics ready
parser = argparse.ArgumentParser(description="POC write/read to a keepass database")
parser.add_argument(help="KeePass database to open",metavar='<KEEPASS_DB>',type=str,dest='keepassdb')
parser.add_argument("--logcfg",help="(Optional) log configuration file for logging", required=False,metavar='<LogCfg_file>',type=str,dest='logcfgfile')
args = parser.parse_args()

# Logger configuration file requested?
if args.logcfgfile:
    plogcfgfile = Path(args.logcfgfile)
    if plogcfgfile.exists():
        with open(plogcfgfile,"rb") as theFile:
            xtmpDict = tomllib.load(theFile)
        logging.config.dictConfig(xtmpDict['logconfig'])
    else:
        print(f"Logging configuration file not found: {plogcfgfile.resolve()}.")
        quit(1)

# Does db file exist
pKeePassDB = Path(args.keepassdb)
logger.debug(f"check if {pKeePassDB.resolve()} exists")
if not pKeePassDB.exists():
    print(f"ERROR: {pKeePassDB.resolve()} Does not exist")
    quit(1)

print(f"Accessing : {pKeePassDB.resolve()}")
logger.info(f"prompt user for password to db {pKeePassDB.resolve()}")
passphrase = getpass.getpass(prompt=" >> Enter password to access file: ",stream=None)

#  Attempt to open database
try:
    kp = PyKeePass(pKeePassDB,password=passphrase)
except pkExceptions.CredentialsError:
    logger.warning("Invalid password provided")
    print("Bad creds")
    quit(1)
except Exception as oopsError:
    logger.critical(f"Unexpected error: {oopsError}",stack_info=True)
    print(f"CRITICAL: Unexpected error {oopsError}")
    traceback.print_exc()
    quit(1)

entryCount = len(kp.entries)
logger.info(f"Total Entries in database: {entryCount}")

main(args)