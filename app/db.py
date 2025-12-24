import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "wms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT, location TEXT, brand TEXT, item_code TEXT,
        item_name TEXT, lot_no TEXT, spec TEXT, qty REAL DEFAULT 0,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tx_type TEXT,
        warehouse TEXT, location TEXT, from_location TEXT, to_location TEXT,
        item_code TEXT, lot_no TEXT, qty REAL, remark TEXT, created_at TEXT
    )""")
    conn.commit()
    conn.close()

# [이력 저장] 모든 컬럼(from/to)이 저장되도록 수정
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark, to_location=None, from_location=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# [조회] 이력 페이지용 함수
def get_history(limit=200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# [입고] 이력 남기기 포함
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty, item_name = excluded.item_name, brand = excluded.brand, spec = excluded.spec
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))
    conn.commit()
    conn.close()
    log_history("IN", warehouse, location, item_code, lot_no, qty, remark)

# [출고] 이력 남기기 포함
def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()
    log_history("OUT", warehouse, location, item_code, lot_no, -qty, remark)

# [이동] 이력 남기기 포함 (from/to 기록)
def move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty, remark="이동"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (qty, warehouse, from_location, item_code, lot_no))
    cur.execute("""
    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no) DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot_no, qty))
    conn.commit()
    conn.close()
    log_history("MOVE", warehouse, from_location, item_code, lot_no, qty, remark, to_location=to_location, from_location=from_location)

# (나머지 get_inventory, dashboard_summary, rollback 등은 기존 유지)
def get_inventory(q=None):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM inventory WHERE 1=1"
    params = []
    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ?)"
        kw = f"%{q}%"
        params = [kw, kw, kw, kw]
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]
    inb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN' AND date(created_at)=date('now','localtime')").fetchone()[0]
    outb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')").fetchone()[0]
    neg = cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0").fetchone()[0]
    conn.close()
    return {"inbound_today": inb, "outbound_today": abs(outb), "total_stock": total, "negative_stock": neg}
