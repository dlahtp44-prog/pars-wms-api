import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "wms.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        location_name TEXT,
        brand TEXT,
        item TEXT,
        name TEXT,
        lot TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        location_name TEXT,
        brand TEXT,
        item TEXT,
        name TEXT,
        lot TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
