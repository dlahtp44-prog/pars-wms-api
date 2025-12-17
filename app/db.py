# app/db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "wms.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        brand TEXT,
        item TEXT,
        item_name TEXT,
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
        item TEXT,
        qty INTEGER,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def log_history(type, item, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO history (type, item, qty, remark, created_at) VALUES (?, ?, ?, ?, ?)",
        (type, item, qty, remark, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
