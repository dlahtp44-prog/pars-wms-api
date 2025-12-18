import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "WMS.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT,
        location TEXT NOT NULL,
        brand TEXT,
        item_code TEXT NOT NULL,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty INTEGER NOT NULL DEFAULT 0,
        UNIQUE(item_code, location, lot_no)
    )
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        location_name TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# ✅ 작업 이력 기록
def log_history(tx_type, row):
    conn = get_conn()
    conn.execute("""
        INSERT INTO history (
            tx_type, location_name, location,
            brand, item_code, item_name, lot_no, spec,
            qty
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type,
        row["location_name"],
        row["location"],
        row["brand"],
        row["item_code"],
        row["item_name"],
        row["lot_no"],
        row["spec"],
        row["qty"]
    ))
    conn.commit()
    conn.close()

def get_history():
    conn = get_conn()
    rows = conn.execute("""
        SELECT *
        FROM history
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return rows
