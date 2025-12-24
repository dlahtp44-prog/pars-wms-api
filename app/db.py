import sqlite3
from datetime import datetime

DB_PATH = "wms.db"


# =========================
# 기본 연결
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
        brand TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        qty REAL,
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
# 재고 조회 (페이지/QR/API 공용)
# =========================
def get_inventory(q: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    if q:
        cur.execute("""
        SELECT * FROM inventory
        WHERE item_code LIKE ? OR item_name LIKE ? OR location LIKE ?
        ORDER BY location, item_code
        """, (f"%{q}%", f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
        SELECT * FROM inventory
        ORDER BY location, item_code
        """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 입고
# =========================
def add_inventory(warehouse, location, brand,
                  item_code, item_name, lot_no, spec, qty):

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
        item_code, lot_no, qty, "입고"
    )

    conn.commit()
    conn.close()


# =========================
# 출고
# =========================
def subtract_inventory(warehouse, location,
                       item_code, lot_no, qty):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, location, item_code, lot_no))

    log_history(
        "OUT", warehouse, location,
        item_code, lot_no, qty, "출고"
    )

    conn.commit()
    conn.close()


# =========================
# 이동
# =========================
def move_inventory(warehouse, from_location, to_location,
                   item_code, lot_no, qty):

    conn = get_conn()
    cur = conn.cursor()

    # 출발지 차감
    cur.execute("""
    UPDATE inventory
    SET qty = qty - ?
    WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (qty, warehouse, from_location, item_code, lot_no))

    # 도착지 증가
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

    log_history(
        "MOVE", warehouse, f"{from_location} → {to_location}",
        item_code, lot_no, qty, "이동"
    )

    conn.commit()
    conn.close()


# =========================
# 이력
# =========================
def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def log_history(tx_type, warehouse, location,
                item_code, lot_no, qty, remark):
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
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT SUM(qty) FROM inventory")
    total_qty = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT item_code) FROM inventory")
    item_count = cur.fetchone()[0] or 0

    cur.execute("""
    SELECT SUM(qty) FROM history
    WHERE tx_type='IN' AND date(created_at)=date('now')
    """)
    inbound_today = cur.fetchone()[0] or 0

    conn.close()

    return {
        "total_qty": total_qty,
        "item_count": item_count,
        "inbound_today": inbound_today
    }
