# app/db.py
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "wms.db"

# =========================
# DB 연결
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

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
# 공통 조회
# =========================
def get_inventory(q: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    if q:
        cur.execute("""
            SELECT * FROM inventory
            WHERE item_code LIKE ? OR item_name LIKE ? OR location LIKE ?
            ORDER BY location
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("SELECT * FROM inventory ORDER BY location")

    rows = cur.fetchall()
    conn.close()
    return rows

def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

# =========================
# 이력 기록
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location,
        item_code, lot_no, qty, remark,
        datetime.now().isoformat(timespec="seconds")
    ))
    conn.commit()
    conn.close()

# =========================
# 입고
# =========================
def add_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty,
    remark="입고"
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

    conn.commit()
    conn.close()

    log_history("IN", warehouse, location, item_code, lot_no, qty, remark)
    return True, "입고 완료"

# =========================
# 출고 (음수 차단)
# =========================
def subtract_inventory(
    warehouse, location, brand,
    item_code, item_name, lot_no, spec, qty,
    remark="출고"
):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT qty FROM inventory
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no))

    row = cur.fetchone()
    current = row[0] if row else 0

    if current < qty:
        conn.close()
        return False, f"재고 부족 (현재 {current}, 요청 {qty})"

    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    conn.commit()
    conn.close()

    log_history("OUT", warehouse, location, item_code, lot_no, qty, remark)
    return True, "출고 완료"

# =========================
# 이동
# =========================
def move_inventory(
    warehouse,
    from_location,
    to_location,
    brand,
    item_code,
    item_name,
    lot_no,
    spec,
    qty
):
    ok, msg = subtract_inventory(
        warehouse, from_location, brand,
        item_code, item_name, lot_no, spec, qty,
        remark=f"이동 출고 → {to_location}"
    )
    if not ok:
        return False, msg

    add_inventory(
        warehouse, to_location, brand,
        item_code, item_name, lot_no, spec, qty,
        remark=f"이동 입고 ← {from_location}"
    )

    return True, "이동 완료"
def get_location_items(warehouse: str, location: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            item_code,
            item_name,
            spec,
            lot_no,
            qty
        FROM inventory
        WHERE warehouse = ?
          AND location = ?
          AND qty > 0
        ORDER BY item_code
    """, (warehouse, location))

    rows = cur.fetchall()
    conn.close()

    return [
        {
            "item_code": r[0],
            "item_name": r[1],
            "spec": r[2],
            "lot_no": r[3],
            "qty": r[4],
        }
        for r in rows
    ]
