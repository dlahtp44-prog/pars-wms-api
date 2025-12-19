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

    # 재고 테이블
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

# =========================
# History 조회
# =========================
def get_history(limit: int = 100):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            tx_type,
            item_code,
            qty,
            location,
            remark,
            created_at
        FROM inventory_tx
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]
]


def log_history(tx_type, item_code, qty, location):
    conn = get_conn()
    conn.execute(
        "INSERT INTO history (tx_type, item_code, qty, location) VALUES (?, ?, ?, ?)",
        (tx_type, item_code, qty, location)
    )
    conn.commit()
    conn.close()

def get_inventory():
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            location_name, brand, item_code, item_name,
            lot_no, spec, location, qty
        FROM inventory
        ORDER BY location, item_code
    """).fetchall()
    conn.close()
    return rows
