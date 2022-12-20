from os import environ

from .database import Sqlite

db_path = environ.get("DB_PATH")

if db_path:
    db = Sqlite(db_path)
else:
    db = Sqlite()
