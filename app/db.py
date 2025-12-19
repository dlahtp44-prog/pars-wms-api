# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "WMS.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # inventory 테이블
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

    # ✅ UNIQUE INDEX (UPSERT 필수)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    # history 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        lot_no TEXT,
        qty REAL,
        remark TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()



# =====================
# 조회 함수들
# =====================

def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            warehouse,
            location,
            brand,
            item_code,
            item_name,
            lot_no,
            spec,
            SUM(qty) as qty
        FROM inventory
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_history(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================
# 이력 기록 (🔥 중요)
# =====================

def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type,
        warehouse,
        location,
        item_code,
        lot_no,
        qty,
        remark
    ))

    conn.commit()
    conn.close()
