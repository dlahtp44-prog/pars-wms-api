import sqlite3
from datetime import datetime

DB_PATH = "app/data/wms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

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
# 이동 처리 핵심
# =========================
def move_inventory(
    warehouse,
    from_location,
    to_location,
    item_code,
    lot_no,
    qty
):
    conn = get_conn()
    cur = conn.cursor()

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # 목적지 증가
    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, brand, item_code, item_name, lot_no, spec, qty)
        SELECT warehouse, ?, brand, item_code, item_name, lot_no, spec, ?
        FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        to_location, qty,
        warehouse, from_location, item_code, lot_no
    ))

    # 이력
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "MOVE", warehouse,
        f"{from_location} → {to_location}",
        item_code, lot_no, qty,
        "QR 이동",
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
