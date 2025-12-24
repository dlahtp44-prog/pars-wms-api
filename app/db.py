import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "WMS.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    conn.commit()
    conn.close()

# 🔹 로케이션별 재고 조회
def get_inventory_by_location(location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT item_code, item_name, lot_no, spec, qty
        FROM inventory
        WHERE location = ?
        ORDER BY item_code
    """, (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
