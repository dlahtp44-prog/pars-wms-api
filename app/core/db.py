import sqlite3

DB_PATH = "WMS.db"

def get_db():
    return sqlite3.connect(DB_PATH)

