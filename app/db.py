# app/db.py
import sqlite3
from datetime import datetime
from typing import List, Dict

DB_PATH = "wms.db"


# =========================
# DB 기본
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
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
        updated_at TEXT,
        UNIQUE(warehouse, location, item_code, lot_no)
    );

    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        from_location TEXT,
        to_location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        created_at TEXT,
        remark TEXT
    );
    """)
    conn.commit()
    conn.close()


# =========================
# 재고 조회
# =========================
def get_inventory(q: str = "") -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM inventory
            WHERE item_code LIKE ? OR item_name LIKE ? OR location LIKE ?
            ORDER BY location, item_code
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM inventory ORDER BY location, item_code")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(location: str) -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM inventory
        WHERE location = ?
        ORDER BY item_code
    """, (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 이력
# =========================
def log_history(
    tx_type: str,
    warehouse: str,
    location: str,
    item_code: str,
    lot_no: str,
    qty: float,
    remark: str = "",
    from_location: str = "",
    to_location: str = "",
    item_name: str = "",
    spec: str = ""
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, from_location, to_location,
         item_code, item_name, lot_no, spec, qty, created_at, remark)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        tx_type, warehouse, location, from_location, to_location,
        item_code, item_name, lot_no, spec, qty,
        datetime.now().isoformat(timespec="seconds"),
        remark
    ))
    conn.commit()
    conn.close()


def get_history() -> List[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def rollback(history_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (history_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return False

    if h["tx_type"] == "IN":
        cur.execute("""
            UPDATE inventory
            SET qty = qty - ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (h["qty"], h["warehouse"], h["location"], h["item_code"], h["lot_no"]))

    elif h["tx_type"] == "OUT":
        cur.execute("""
            UPDATE inventory
            SET qty = qty + ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (h["qty"], h["warehouse"], h["location"], h["item_code"], h["lot_no"]))

    elif h["tx_type"] == "MOVE":
        cur.execute("""
            UPDATE inventory SET qty = qty + ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (h["qty"], h["warehouse"], h["from_location"], h["item_code"], h["lot_no"]))

        cur.execute("""
            UPDATE inventory SET qty = qty - ?
            WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        """, (h["qty"], h["warehouse"], h["to_location"], h["item_code"], h["lot_no"]))

    cur.execute("DELETE FROM history WHERE id=?", (history_id,))
    conn.commit()
    conn.close()
    return True


# =========================
# 재고 처리 (입고/출고/이동)
# =========================
def add_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty,
            updated_at = excluded.updated_at
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no, spec,
        qty, datetime.now().isoformat(timespec="seconds")
    ))
    conn.commit()
    conn.close()


def subtract_inventory(
    warehouse, location, item_code, lot_no, qty,
    block_negative: bool = True
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))
    row = cur.fetchone()

    if not row:
        conn.close()
        raise ValueError("재고 없음")

    if block_negative and row["qty"] < qty:
        conn.close()
        raise ValueError("재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()


def move_inventory(
    warehouse, from_location, to_location,
    item_code, lot_no, qty
):
    subtract_inventory(warehouse, from_location, item_code, lot_no, qty)
    add_inventory(warehouse, to_location, "", item_code, "", lot_no, "", qty)


# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total_stock = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='IN'
        AND date(created_at)=date('now')
    """)
    inbound_today = cur.fetchone()[0]

    cur.execute("""
        SELECT IFNULL(SUM(qty),0)
        FROM history
        WHERE tx_type='OUT'
        AND date(created_at)=date('now')
    """)
    outbound_today = cur.fetchone()[0]

    conn.close()

    return {
        "total_stock": total_stock,
        "inbound_today": inbound_today,
        "outbound_today": outbound_today
    }


# =========================
# 관리자
# =========================
def admin_password_ok(pw: str) -> bool:
    return pw == "admin123"
