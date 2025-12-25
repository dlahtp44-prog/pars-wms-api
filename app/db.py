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
def get_inventory():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      SELECT warehouse, location, item_code, item_name,
             lot_no, spec, brand, qty
      FROM inventory
      ORDER BY item_code
    """)
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "warehouse": r[0],
            "location": r[1],
            "item_code": r[2],
            "item_name": r[3],
            "lot_no": r[4],
            "spec": r[5],
            "brand": r[6],
            "qty": r[7],
        }
        for r in rows
    ]


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
def move_inventory(warehouse, item_code, lot_no, qty, from_location, to_location):
    conn = get_conn()
    cur = conn.cursor()

    # 출발지 차감
    cur.execute("""
        UPDATE inventory
        SET qty = qty - ?
        WHERE warehouse=? AND item_code=? AND lot_no=? AND location=?
    """, (qty, warehouse, item_code, lot_no, from_location))

    # 도착지 증가
    cur.execute("""
        INSERT INTO inventory (warehouse, location, item_code, lot_no, qty)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot_no, qty))

    # 이력
    cur.execute("""
        INSERT INTO history (tx_type, warehouse, location, item_code, lot_no, qty, remark)
        VALUES ('MOVE', ?, ?, ?, ?, ?, ?)
    """, (
        warehouse,
        f"{from_location}→{to_location}",
        item_code,
        lot_no,
        qty,
        "QR 이동"
    ))

    conn.commit()
    conn.close()
def get_locations():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      SELECT DISTINCT warehouse, location
      FROM inventory
      ORDER BY warehouse, location
    """)
    rows = cur.fetchall()
    conn.close()

    return [
        {"warehouse": r[0], "location": r[1]}
        for r in rows
    ]

