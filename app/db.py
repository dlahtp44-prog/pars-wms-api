import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("app/data/wms.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cur = conn.cursor()

    # 재고
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL DEFAULT 0,
        updated_at TEXT,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )
    """)

    # 이력
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

# =====================
# 공통 DB 함수들
# =====================

def get_inventory():
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM inventory
        ORDER BY item_code, lot_no
    """).fetchall()
    conn.close()
    return rows

def get_inventory_by_location(location: str):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM inventory
        WHERE location = ?
    """, (location,)).fetchall()
    conn.close()
    return rows

def get_history(limit: int = 300):
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM history
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows

def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    conn.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        tx_type, warehouse, location,
        item_code, lot_no, qty,
        remark, datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

# =====================
# 입고 / 출고 / 이동
# =====================

def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty):
    conn = get_conn()
    conn.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET
            qty = qty + excluded.qty,
            updated_at = excluded.updated_at
    """, (
        warehouse, location, brand,
        item_code, item_name, lot_no,
        spec, qty, datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def subtract_inventory(warehouse, location, item_code, lot_no, qty):
    conn = get_conn()
    conn.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()

def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty):
    subtract_inventory(warehouse, from_loc, item_code, lot_no, qty)
    add_inventory(warehouse, to_loc, "", item_code, "", lot_no, "", qty)

# =====================
# 대시보드
# =====================

def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    inbound = cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='IN' AND date(created_at)=date('now')
    """).fetchone()[0]

    outbound = cur.execute("""
        SELECT IFNULL(SUM(qty),0) FROM history
        WHERE tx_type='OUT' AND date(created_at)=date('now')
    """).fetchone()[0]

    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]

    conn.close()
    return inbound, outbound, total

# =====================
# 관리자
# =====================

def admin_password_ok(pw: str):
    return pw == "admin123"   # 나중에 env로 변경
