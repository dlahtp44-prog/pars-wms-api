# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"


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

    # history
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

    # UPSERT용 UNIQUE INDEX
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
    """)

    conn.commit()
    conn.close()


# =====================
# 재고 조회
# =====================
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            warehouse, location, brand,
            item_code, item_name, lot_no, spec,
            SUM(qty) AS qty
        FROM inventory
        GROUP BY warehouse, location, item_code, lot_no
        ORDER BY item_code
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =====================
# 이력 조회
# =====================
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
# 이력 기록
# =====================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, item_code, lot_no, qty, remark))
    conn.commit()
    conn.close()


# =====================
# 이력 롤백 (관리자)
# =====================
def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return

    # 반대 트랜잭션
    reverse_qty = -row["qty"]
    cur.execute("""
        UPDATE inventory
        SET qty = qty + ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        reverse_qty,
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()


# =====================
# 대시보드 요약
# =====================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN'
          AND date(created_at)=date('now')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT'
          AND date(created_at)=date('now')
    """)
    outbound = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()
    return inbound, outbound, total, negative
