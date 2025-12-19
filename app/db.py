import sqlite3

DB_PATH = "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
      location_name TEXT,
      brand TEXT,
      item_code TEXT,
      item_name TEXT,
      lot_no TEXT,
      spec TEXT,
      location TEXT,import sqlite3
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
        location_name TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        location TEXT,
        qty INTEGER,
        PRIMARY KEY (item_code, location)
    )
    """)

    # history
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        item_code TEXT,
        qty INTEGER,
        location TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ✅ 재고 조회 (inventory_page, worker_inventory 등)
def get_inventory():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            location_name,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            location,
            qty
        FROM inventory
        ORDER BY location, item_code
    """).fetchall()
    conn.close()
    return rows


# ✅ 작업이력 조회 (모든 page / api 공용)
def get_history():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            tx_type,
            item_code,
            qty,
            location,
            created_at
        FROM history
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return rows


# ✅ 작업이력 기록
def log_history(tx_type, item_code, qty, location):
    conn = get_conn()
    conn.execute("""
        INSERT INTO history (tx_type, item_code, qty, location)
        VALUES (?, ?, ?, ?)
    """, (tx_type, item_code, qty, location))
    conn.commit()
    conn.close()

      qty INTEGER DEFAULT 0,
      PRIMARY KEY (item_code, location)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      tx_type TEXT,
      item_code TEXT,
      qty INTEGER,
      location TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def log_history(tx_type, item_code, qty, location):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (tx_type, item_code, qty, location)
        VALUES (?, ?, ?, ?)
    """, (tx_type, item_code, qty, location))
    conn.commit()
    conn.close()

def get_inventory():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM inventory
        ORDER BY item_code, location
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
