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

# --- 필수 함수: 조회 관련 ---
def get_inventory(q=None):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM inventory WHERE qty != 0"
    params = []
    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR location LIKE ?)"
        kw = f"%{q}%"
        params = [kw, kw, kw]
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit=500):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_location_items(location: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE location=? AND qty > 0", (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- 필수 함수: 처리 관련 ---
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty, item_name = excluded.item_name
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))
    cur.execute("INSERT INTO history (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at) VALUES ('IN', ?, ?, ?, ?, ?, ?, ?)",
                (warehouse, location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (qty, warehouse, location, item_code, lot_no))
    cur.execute("INSERT INTO history (tx_type, warehouse, location, item_code, lot_no, qty, remark, created_at) VALUES ('OUT', ?, ?, ?, ?, ?, ?, ?)",
                (warehouse, location, item_code, lot_no, -qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty, remark="이동"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (qty, warehouse, from_loc, item_code, lot_no))
    cur.execute("""
    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no) DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_loc, item_code, lot_no, qty))
    cur.execute("INSERT INTO history (tx_type, warehouse, location, from_location, to_location, item_code, lot_no, qty, remark, created_at) VALUES ('MOVE', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (warehouse, from_loc, from_loc, to_loc, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --- 필수 함수: 기타 ---
def admin_password_ok(pw: str):
    return pw == "admin123"

def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]
    inb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN' AND date(created_at)=date('now','localtime')").fetchone()[0]
    outb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')").fetchone()[0]
    conn.close()
    return {"inbound_today": inb, "outbound_today": abs(outb), "total_stock": total}
