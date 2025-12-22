# app/db.py
import sqlite3
from pathlib import Path
from typing import List, Dict

DB_PATH = Path(__file__).parent.parent / "WMS.db"


# =====================
# DB 연결
# =====================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =====================
# DB 초기화
# =====================
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

    # UNIQUE (UPSERT용)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS ux_inventory
    ON inventory (warehouse, location, item_code, lot_no)
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


# =====================
# 재고 조회
# =====================
def get_inventory() -> List[Dict]:
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
def get_history(limit: int = 200) -> List[Dict]:
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
# 이력 기록 (공용)
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
    """, (tx_type, warehouse, location, item_code, lot_no, qty, remark))
    conn.commit()
    conn.close()


# =====================
# 공용 재고 처리 (입고/출고/이동/QR)
# =====================
def add_inventory(
    tx_type: str,          # IN | OUT | MOVE | 입고 | 출고 | 이동
    warehouse: str,
    location: str,
    item_code: str,
    item_name: str,
    lot_no: str,
    spec: str,
    qty: float,
    remark: str = ""
):
    conn = get_conn()
    cur = conn.cursor()

    # 출고 / 이동 → 음수 방지
    if tx_type in ("OUT", "출고", "MOVE", "이동"):
        cur.execute("""
            SELECT IFNULL(SUM(qty),0)
            FROM inventory
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (warehouse, location, item_code, lot_no))
        current_qty = cur.fetchone()[0]

        if current_qty < qty:
            conn.close()
            raise ValueError("재고 부족 (음수 방지)")

        qty = -qty

    # UPSERT
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, '', ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, location,
        item_code, item_name,
        lot_no, spec,
        qty
    ))

    # 이력
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


# =====================
# 롤백 (관리자)
# =====================
def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (history_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("이력 없음")

    revert_qty = -row["qty"]

    cur.execute("""
        UPDATE inventory
        SET qty = qty + ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        revert_qty,
        row["warehouse"],
        row["location"],
        row["item_code"],
        row["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
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
        WHERE tx_type IN ('IN','입고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type IN ('OUT','출고')
          AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative_stock = cur.fetchone()[0]

    conn.close()

    return {
        "inbound_today": inbound_today,
        "outbound_today": outbound_today,
        "total_stock": total_stock,
        "negative_stock": negative_stock
    }


# =====================
# 대시보드 그래프 (최근 N일)
# =====================
def dashboard_trend(days: int = 7):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
          DATE(created_at) as d,
          SUM(CASE WHEN tx_type IN ('IN','입고') THEN qty ELSE 0 END) as inbound,
          SUM(CASE WHEN tx_type IN ('OUT','출고') THEN qty ELSE 0 END) as outbound
        FROM history
        WHERE DATE(created_at) >= DATE('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY d
    """, (f"-{days} day",))

    rows = cur.fetchall()
    conn.close()

    return [
        {"date": r["d"], "inbound": r["inbound"], "outbound": r["outbound"]}
        for r in rows
    ]
