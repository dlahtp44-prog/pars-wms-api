# app/db.py
import sqlite3
from datetime import datetime

DB_PATH = "WMS.db"

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

    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tx_type TEXT,
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# -------------------------
# 재고 조회
# -------------------------
def get_inventory(q: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    if q:
        cur.execute("""
        SELECT * FROM inventory
        WHERE item_code LIKE ? OR item_name LIKE ?
        ORDER BY item_code
        """, (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM inventory ORDER BY item_code")

    rows = cur.fetchall()
    conn.close()
    return rows


# -------------------------
# 입고
# -------------------------
def add_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no, spec, qty
    ))

    log_history(
        "IN", warehouse, location,
        item_code, item_name, lot_no, spec, qty
    )

    conn.commit()
    conn.close()


# -------------------------
# 출고
# -------------------------
def subtract_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history(
        "OUT", warehouse, location,
        item_code, item_name, lot_no, spec, qty
    )

    conn.commit()
    conn.close()


# -------------------------
# 이동
# -------------------------
def move_inventory(
    warehouse, from_location, to_location,
    brand, item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()

    # 차감
    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # 증가
    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, to_location, brand,
        item_code, item_name, lot_no, spec, qty
    ))

    log_history(
        "MOVE", warehouse, f"{from_location}->{to_location}",
        item_code, item_name, lot_no, spec, qty
    )

    conn.commit()
    conn.close()


# -------------------------
# 이력
# -------------------------
def log_history(
    tx_type, warehouse, location,
    item_code, item_name, lot_no, spec, qty
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO history
    (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location,
        item_code, item_name, lot_no, spec, qty,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# -------------------------
# 대시보드
# -------------------------
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("""
    SELECT IFNULL(SUM(qty),0) FROM history
    WHERE tx_type='IN' AND date(created_at)=date('now')
    """)
    inbound = cur.fetchone()[0]

    cur.execute("""
    SELECT IFNULL(SUM(qty),0) FROM history
    WHERE tx_type='OUT' AND date(created_at)=date('now')
    """)
    outbound = cur.fetchone()[0]

    conn.close()
    return inbound, outbound, total
