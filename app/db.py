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

# --- 1. 라우터 충돌 방지용 로그 함수 (log_history) ---
def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark, to_location=None, from_location=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# --- 2. 대시보드 충돌 방지용 함수 (negative_stock 포함) ---
def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]
    inb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN' AND date(created_at)=date('now','localtime')").fetchone()[0]
    outb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')").fetchone()[0]
    # 템플릿 에러 방지를 위해 반드시 추가
    neg = cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0").fetchone()[0]
    conn.close()
    return {
        "inbound_today": inb, 
        "outbound_today": abs(outb), 
        "total_stock": total,
        "negative_stock": neg  # 이 값이 있어야 dashboard.html이 열립니다.
    }

# --- 3. 기본 조회/처리 함수 유지 ---
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

def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inventory VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty, item_name = excluded.item_name
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))
    conn.commit()
    conn.close()
    log_history('IN', warehouse, location, item_code, lot_no, qty, remark)

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()
    log_history('OUT', warehouse, location, item_code, lot_no, -qty, remark)

def get_history(limit=500):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def admin_password_ok(pw: str):
    return pw == "admin123"
