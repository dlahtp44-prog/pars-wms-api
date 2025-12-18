import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "WMS.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        item_code TEXT,
        item_name TEXT,
        brand TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        PRIMARY KEY (item_code, lot_no, location)
    )
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty INTEGER,
        location TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def log_history(cur, tx_type, item_code, lot_no, qty, location):
    cur.execute("""
        INSERT INTO history (tx_type, item_code, lot_no, qty, location)
        VALUES (?, ?, ?, ?, ?)
    """, (tx_type, item_code, lot_no, qty, location))
