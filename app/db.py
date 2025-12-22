# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "WMS.db"


# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# DB 초기화
# =========================
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

    conn.commit()
    conn.close()


# =========================
# 재고 조회
# =========================
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


# =========================
# 작업 이력 조회
# =========================
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


# =========================
# 작업 이력 기록 (모든 router 공용)
# =========================
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


# =========================
# ✅ 대시보드 요약 (🔥 핵심)
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    # 오늘 입고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type IN ('IN','입고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = cur.fetchone()[0]

    # 오늘 출고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type IN ('OUT','출고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = cur.fetchone()[0]

    # 총 재고
    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM inventory
    """)
    total_stock = cur.fetchone()[0]

    # 음수 재고
    cur.execute("""
        SELECT COUNT(*)
        FROM inventory
        WHERE qty < 0
    """)
    negative_stock = cur.fetchone()[0]

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock
    }
