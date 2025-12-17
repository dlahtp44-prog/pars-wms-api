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
        item_code TEXT PRIMARY KEY,
        warehouse TEXT,
        brand TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        warehouse TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

def log_history(t, data):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history
    (type, warehouse, brand, item_code, item_name, lot_no, spec, location, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        t,
        data["warehouse"],
        data["brand"],
        data["item_code"],
        data["item_name"],
        data["lot_no"],
        data["spec"],
        data["location"],
        data["qty"],
        data.get("remark", ""),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
