# app/db.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "WMS.db"

# -------------------------
# 기본 커넥션
# -------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# DB 초기화
# -------------------------
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse TEXT DEFAULT 'MAIN',
        location TEXT,
        brand TEXT,
        item_code TEXT NOT NULL,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(warehouse, location, item_code, lot_no)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        remark TEXT,
        rolled_back INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# 공통: 이력 기록
# -------------------------
def _log_history(**kwargs):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history
    (tx_type, warehouse, location, from_location, to_location,
     brand, item_code, item_name, lot_no, spec, qty, remark)
    VALUES
    (:tx_type, :warehouse, :location, :from_location, :to_location,
     :brand, :item_code, :item_name, :lot_no, :spec, :qty, :remark)
    """, kwargs)

    conn.commit()
    conn.close()


# -------------------------
# 입고
# -------------------------
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET
        qty = qty + excluded.qty,
        updated_at=CURRENT_TIMESTAMP
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))

    conn.commit()
    conn.close()

    _log_history(
        tx_type="IN",
        warehouse=warehouse,
        location=location,
        from_location="",
        to_location="",
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=remark or "입고"
    )


# -------------------------
# 출고
# -------------------------
def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT qty FROM inventory
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    if not row or row["qty"] < qty:
        conn.close()
        raise ValueError("재고 부족")

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?, updated_at=CURRENT_TIMESTAMP
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    _log_history(
        tx_type="OUT",
        warehouse=warehouse,
        location=location,
        from_location="",
        to_location="",
        brand="",
        item_code=item_code,
        item_name="",
        lot_no=lot_no,
        spec="",
        qty=qty,
        remark=remark or "출고"
    )


# -------------------------
# 이동
# -------------------------
def move_inventory(warehouse, from_location, to_location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    subtract_inventory(warehouse, from_location, item_code, lot_no, qty, "이동 출발")

    add_inventory(
        warehouse, to_location, brand,
        item_code, item_name, lot_no, spec, qty,
        remark="이동 도착"
    )

    _log_history(
        tx_type="MOVE",
        warehouse=warehouse,
        location=f"{from_location}→{to_location}",
        from_location=from_location,
        to_location=to_location,
        brand=brand,
        item_code=item_code,
        item_name=item_name,
        lot_no=lot_no,
        spec=spec,
        qty=qty,
        remark=remark or "이동"
    )


# -------------------------
# 재고 조회 (항상 list[dict])
# -------------------------
def get_inventory() -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT warehouse, location, brand, item_code, item_name,
           lot_no, spec, SUM(qty) AS qty
    FROM inventory
    GROUP BY warehouse, location, item_code, lot_no
    ORDER BY item_code, lot_no
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------
# 이력 조회
# -------------------------
def get_history(limit=500) -> List[Dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM history
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------
# 대시보드 (⭐ 항상 dict 반환 ⭐)
# -------------------------
def dashboard_summary() -> Dict[str, Any]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    cur.execute("""
    SELECT IFNULL(SUM(qty),0) FROM history
    WHERE tx_type='IN' AND DATE(created_at)=DATE('now','localtime')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
    SELECT IFNULL(SUM(qty),0) FROM history
    WHERE tx_type='OUT' AND DATE(created_at)=DATE('now','localtime')
    """)
    outbound_today = cur.fetchone()[0]

    conn.close()

    return {
        "total_stock": total_stock,
        "inbound_today": inbound_today,
        "outbound_today": outbound_today
    }


# -------------------------
# 관리자
# -------------------------
def admin_password_ok(pw: str) -> bool:
    return pw == "1234"
