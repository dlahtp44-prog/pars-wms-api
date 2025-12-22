import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent.parent / "WMS.db"

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
        qty REAL DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        created_at DATE DEFAULT (DATE('now'))
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# 재고 조회
# -------------------------
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT item_code, lot_no, SUM(qty) as qty
        FROM inventory
        GROUP BY item_code, lot_no
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------
# 대시보드용 집계
# -------------------------
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    today = date.today().isoformat()

    cur.execute("SELECT SUM(qty) FROM history WHERE tx_type='IN' AND created_at=?", (today,))
    inbound = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(qty) FROM history WHERE tx_type='OUT' AND created_at=?", (today,))
    outbound = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(qty) FROM inventory")
    total = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0] or 0

    conn.close()
    return inbound, outbound, total, negative


# -------------------------
# 이력 기록
# -------------------------
def log_history(tx_type, warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history (tx_type, warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, item_code, lot_no, qty))
    conn.commit()
    conn.close()
