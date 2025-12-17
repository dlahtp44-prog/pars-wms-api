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

    # 재고 테이블 (location 포함)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item TEXT PRIMARY KEY,
        qty INTEGER,
        location TEXT
    )
    """)

    # 작업 이력 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        item TEXT,
        qty INTEGER,
        location TEXT,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_history(type, item, qty, location="", remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO history (type, item, qty, location, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (type, item, qty, location, remark, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()

