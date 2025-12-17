# app/db.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "wms.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 품목
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        code TEXT
    )
    """)

    # 재고
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_code TEXT,
        location TEXT,
        qty INTEGER
    )
    """)

    # 이력
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()
