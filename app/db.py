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

def admin_password_ok(password: str):
    return password == "admin1234"

# --- 재고 관련 ---
def get_inventory(q=None):
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT * FROM inventory WHERE qty != 0"
    params = []
    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR location LIKE ?)"
        kw = f"%{q}%"
        params = [kw, kw, kw]
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- 이력 관련 ---
def get_history(limit=500):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history_for_excel():
    """이력을 한글 필드명으로 변환하여 엑셀용으로 추출"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            CASE tx_type WHEN 'IN' THEN '입고' WHEN 'OUT' THEN '출고' WHEN 'MOVE' THEN '이동' ELSE tx_type END as 구분,
            warehouse as 창고, location as 위치, from_location as 출발지, to_location as 도착지,
            item_code as 품번, lot_no as LOT, qty as 수량, remark as 비고, created_at as 시간
        FROM history ORDER BY created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# --- 입/출/이동 로직 (기존 유지) ---
def add_inventory(warehouse, location, brand, item_code, item_name, lot_no, spec, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(warehouse, location, item_code, lot_no)
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

def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty, remark="이동"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (qty, warehouse, from_loc, item_code, lot_no))
    cur.execute("INSERT INTO inventory (warehouse, location, item_code, lot_no, qty) VALUES (?, ?, ?, ?, ?) ON CONFLICT(warehouse, location, item_code, lot_no) DO UPDATE SET qty = qty + excluded.qty", (warehouse, to_loc, item_code, lot_no, qty))
    conn.commit()
    conn.close()
    log_history('MOVE', warehouse, from_loc, item_code, lot_no, qty, remark, to_location=to_loc, from_location=from_loc)

def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark, to_location=None, from_location=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO history (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def rollback_inventory(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    h = cur.fetchone()
    if h:
        if h['tx_type'] == 'IN':
            cur.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=?", (h['qty'], h['location'], h['item_code'], h['lot_no']))
        elif h['tx_type'] == 'OUT':
            cur.execute("UPDATE inventory SET qty = qty + ? WHERE location=? AND item_code=? AND lot_no=?", (abs(h['qty']), h['location'], h['item_code'], h['lot_no']))
        elif h['tx_type'] == 'MOVE':
            cur.execute("UPDATE inventory SET qty = qty + ? WHERE location=? AND item_code=? AND lot_no=?", (h['qty'], h['from_location'], h['item_code'], h['lot_no']))
            cur.execute("UPDATE inventory SET qty = qty - ? WHERE location=? AND item_code=? AND lot_no=?", (h['qty'], h['to_location'], h['item_code'], h['lot_no']))
        cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True
