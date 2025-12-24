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
    print("✅ DB 초기화 및 테이블 확인 완료")

# =========================
# 1. 조회 기능 (재고/이력/로케이션)
# =========================

def get_inventory(q: str | None = None):
    """재고 조회용 (검색 기능 포함)"""
    conn = get_conn()
    cur = conn.cursor()
    # 수량이 0이 아닌 것만 표시하거나, 전체를 표시하도록 설정 가능
    sql = "SELECT * FROM inventory WHERE 1=1"
    params = []
    if q:
        sql += " AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ?)"
        kw = f"%{q}%"
        params = [kw, kw, kw, kw]
    sql += " ORDER BY item_code ASC"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_history(limit=200):
    """작업 이력 조회용"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_location_items(location: str):
    """특정 로케이션의 재고 확인 (QR 상세페이지용)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE location=? AND qty != 0", (location,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =========================
# 2. 핵심 물류 처리 로직
# =========================

def log_history(tx_type, warehouse, location, item_code, lot_no, qty, remark, to_location=None, from_location=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO history (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_type, warehouse, location, to_location, from_location, item_code, lot_no, qty, remark, datetime.now().isoformat()))
    conn.commit()
    conn.close()

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

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()
    log_history("OUT", warehouse, location, item_code, lot_no, -qty, remark)

def move_inventory(warehouse, from_location, to_location, item_code, lot_no, qty, remark="이동"):
    conn = get_conn()
    cur = conn.cursor()
    # 기존 위치 차감
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (qty, warehouse, from_location, item_code, lot_no))
    # 새 위치 가산
    cur.execute("""
    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no) DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_location, item_code, lot_no, qty))
    conn.commit()
    conn.close()
    log_history("MOVE", warehouse, from_location, item_code, lot_no, qty, remark, to_location=to_location, from_location=from_location)

# =========================
# 3. 대시보드 및 관리 기능
# =========================

def dashboard_summary():
    conn = get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]
    inb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN' AND date(created_at)=date('now','localtime')").fetchone()[0]
    outb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')").fetchone()[0]
    neg = cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0").fetchone()[0]
    conn.close()
    return {"inbound_today": inb, "outbound_today": abs(outb), "total_stock": total, "negative_stock": neg}

def rollback(tx_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM history WHERE id=?", (tx_id,))
    h = cur.fetchone()
    if h:
        if h["tx_type"] == "IN":
            cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (h["qty"], h["warehouse"], h["location"], h["item_code"], h["lot_no"]))
        elif h["tx_type"] == "OUT":
            cur.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (abs(h["qty"]), h["warehouse"], h["location"], h["item_code"], h["lot_no"]))
        elif h["tx_type"] == "MOVE":
            cur.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (h["qty"], h["warehouse"], h["from_location"], h["item_code"], h["lot_no"]))
            cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", (h["qty"], h["warehouse"], h["to_location"], h["item_code"], h["lot_no"]))
        cur.execute("DELETE FROM history WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()

def admin_password_ok(pw: str) -> bool:
    return pw == "admin123"
