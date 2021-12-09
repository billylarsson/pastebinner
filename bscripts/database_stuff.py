from bscripts.sqlite_handler import SQLite
import os

sqlite = SQLite(
    DATABASE_FILENAME=os.environ['DATABASE_FILENAME'],
    DATABASE_FOLDER=os.environ['DATABASE_FOLDER'],
    DATABASE_SUBFOLDER=os.environ['DATABASE_SUBFOLDER'],
    INI_FILENAME=os.environ['INI_FILENAME'],
    INI_FILE_DIR=os.environ['INI_FILE_DIR'],
)

class DB: # local database
    class settings:
        config = sqlite.db_sqlite('settings', 'config', 'blob')

    class pastes:
        paste_date = sqlite.db_sqlite('pastes', 'paste_date', 'integer')
        paste_expire_date = sqlite.db_sqlite('pastes', 'paste_expire_date', 'integer')
        paste_format_long = sqlite.db_sqlite('pastes', 'paste_format_long')
        paste_format_short = sqlite.db_sqlite('pastes', 'paste_format_short')
        paste_hits = sqlite.db_sqlite('pastes', 'paste_hits', 'integer')
        paste_key = sqlite.db_sqlite('pastes', 'paste_key')
        paste_private = sqlite.db_sqlite('pastes', 'paste_private', 'integer')
        paste_size = sqlite.db_sqlite('pastes', 'paste_size', 'integer')
        paste_title = sqlite.db_sqlite('pastes', 'paste_title')
        paste_url = sqlite.db_sqlite('pastes', 'paste_url')
        username = sqlite.db_sqlite('pastes', 'username')
        contents = sqlite.db_sqlite('pastes', 'contents')
