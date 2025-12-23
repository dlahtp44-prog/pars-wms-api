# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "WMS.db"

# =====================
# DB 연결
# =====================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =====================
# 초기화
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
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        UNIQUE(warehouse, location, item_code, lot_no)
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

# =====================
# 재고 조회
# =====================
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT warehouse, location, item_code, item_name, lot_no, spec, SUM(qty) qty
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
        SELECT * FROM history
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
# 입고 (증가)
# =====================
def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, item_name, lot_no, spec, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, location, item_code, item_name, lot_no, spec, qty))
    conn.commit()
    conn.close()

# =====================
# 출고 (차감 + 음수 방지)
# =====================
def subtract_inventory(warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    if not row or row["qty"] < qty:
        conn.close()
        raise Exception("재고 부족")

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()
