# app/db.py
import sqlite3
from datetime import datetime

DB_PATH = "app/wms.db"


# =========================
# DB 연결
# =========================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# 초기화
# =========================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT,
        location TEXT,
        item_code TEXT,
        item_name TEXT,
        lot_no TEXT,
        spec TEXT,
        brand TEXT,
        qty REAL,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    );

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
    );
    """)
    conn.commit()
    conn.close()


# =========================
# 재고 조회
# =========================
def get_inventory(keyword: str = ""):
    conn = get_conn()
    cur = conn.cursor()

    if keyword:
        cur.execute("""
            SELECT * FROM inventory
            WHERE item_code LIKE ? OR item_name LIKE ? OR location LIKE ?
            ORDER BY location
        """, (f"%{keyword}%",)*3)
    else:
        cur.execute("SELECT * FROM inventory ORDER BY location")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_location_items(location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM inventory
        WHERE location=?
        ORDER BY item_code
    """, (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# =========================
# 이력
# =========================
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO history
        (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tx_type, warehouse, location,
        item_code, lot_no, qty, remark,
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_history():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        return False

    qty = h["qty"]
    sign = -1 if h["tx_type"] == "IN" else 1

    cur.execute("""
        UPDATE inventory
        SET qty = qty + ?
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (
        qty * sign,
        h["warehouse"], h["location"],
        h["item_code"], h["lot_no"]
    ))

    cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True


# =========================
# 입고 / 출고 / 이동
# =========================
def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, brand, qty):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory
        (warehouse, location, item_code, item_name, lot_no, spec, brand, qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(warehouse, location, item_code, lot_no)
        DO UPDATE SET qty = qty + excluded.qty
    """, (
        warehouse, location,
        item_code, item_name, lot_no, spec, brand, qty
    ))

    log_history("IN", warehouse, location, item_code, lot_no, qty, "입고")
    conn.commit()
    conn.close()


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


def move_inventory(warehouse, item_code, lot_no, from_loc, to_loc, qty):
    subtract_inventory(warehouse, from_loc, item_code, lot_no, qty)
    add_inventory(warehouse, to_loc, item_code, "", lot_no, "", "", qty)
    log_history("MOVE", warehouse, to_loc, item_code, lot_no, qty, "이동")


# =========================
# 대시보드
# =========================
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory")
    total = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN'")
    inbound = cur.fetchone()[0]

    cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT'")
    outbound = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0")
    negative = cur.fetchone()[0]

    conn.close()
    return inbound, outbound, total, negative
