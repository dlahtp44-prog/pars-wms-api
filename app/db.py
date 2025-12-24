import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("wms.db")

# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        brand TEXT,
        qty REAL DEFAULT 0,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
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
        remark TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# 재고 조회
# =========================
def get_inventory(warehouse=None, location=None):
    conn = get_conn()
    cur = conn.cursor()

    sql = "SELECT * FROM inventory WHERE 1=1"
    params = []

    if warehouse:
        sql += " AND warehouse=?"
        params.append(warehouse)

    if location:
        sql += " AND location=?"
        params.append(location)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 이력 조회
# =========================
def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 공통 이력 기록
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        tx_type, warehouse, location, item_code, lot_no, qty, remark,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

# =========================
# 입고
# =========================
def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, brand, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory
    (warehouse, location, item_code, item_name, lot_no, spec, brand, qty)
    VALUES (?,?,?,?,?,?,?,?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, location, item_code, item_name, lot_no, spec, brand, qty
    ))

    log_history("IN", warehouse, location, item_code, lot_no, qty, "입고")
    conn.commit()
    conn.close()

# =========================
# 출고
# =========================
def subtract_inventory(warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history("OUT", warehouse, location, item_code, lot_no, qty, "출고")
    conn.commit()
    conn.close()

# =========================
# 이동
# =========================
def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty):
    subtract_inventory(warehouse, from_loc, item_code, lot_no, qty)
    add_inventory(warehouse, to_loc, item_code, "", lot_no, "", "", qty)
    log_history("MOVE", warehouse, to_loc, item_code, lot_no, qty, f"{from_loc} → {to_loc}")
