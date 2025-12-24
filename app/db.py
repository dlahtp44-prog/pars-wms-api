import sqlite3
from pathlib import Path
from datetime import datetime

# 데이터베이스 파일 경로 설정
DB_PATH = Path(__file__).parent / "wms.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # 재고 테이블: 창고, 로케이션, 품번, LOT를 기준으로 유일성 유지
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        warehouse TEXT, location TEXT, brand TEXT, item_code TEXT,
        item_name TEXT, lot_no TEXT, spec TEXT, qty REAL DEFAULT 0,
        PRIMARY KEY (warehouse, location, item_code, lot_no)
    )""")
    # 이력 테이블: 모든 입/출/이동 기록 저장
    cur.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tx_type TEXT,
        warehouse TEXT, location TEXT, from_location TEXT, to_location TEXT,
        item_code TEXT, lot_no TEXT, qty REAL, remark TEXT, created_at TEXT
    )""")
    conn.commit()
    conn.close()

# --- 관리자 보안 함수 ---
def admin_password_ok(password: str):
    """관리자 페이지 접속 비밀번호 확인"""
    return password == "admin1234"

# --- 핵심 물류 로직 ---

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
    """입고 처리: 기존 재고가 있으면 더하고 없으면 새로 생성"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO inventory (warehouse, location, brand, item_code, item_name, lot_no, spec, qty) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no)
    DO UPDATE SET qty = qty + excluded.qty, item_name = excluded.item_name
    """, (warehouse, location, brand, item_code, item_name, lot_no, spec, qty))
    conn.commit()
    conn.close()
    log_history('IN', warehouse, location, item_code, lot_no, qty, remark)

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark=""):
    """출고 처리: 재고 차감"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", 
                (qty, warehouse, location, item_code, lot_no))
    conn.commit()
    conn.close()
    log_history('OUT', warehouse, location, item_code, lot_no, -qty, remark)

def move_inventory(warehouse, from_loc, to_loc, item_code, lot_no, qty, remark="이동"):
    """이동 처리: 출발지 차감 및 도착지 가산 (QR 이동 핵심 로직)"""
    conn = get_conn()
    cur = conn.cursor()
    # 1. 출발지 차감
    cur.execute("UPDATE inventory SET qty = qty - ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?", 
                (qty, warehouse, from_loc, item_code, lot_no))
    # 2. 도착지 가산
    cur.execute("""
    INSERT INTO inventory (warehouse, location, item_code, lot_no, qty) VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(warehouse, location, item_code, lot_no) DO UPDATE SET qty = qty + excluded.qty
    """, (warehouse, to_loc, item_code, lot_no, qty))
    conn.commit()
    conn.close()
    log_history('MOVE', warehouse, from_loc, item_code, lot_no, qty, remark, to_location=to_loc, from_location=from_loc)

# --- 데이터 조회 및 관리 로직 ---

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

def get_location_items(location: str):
    """특정 로케이션의 재고 목록 조회 (QR 스캔용)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inventory WHERE location=? AND qty > 0", (location,))
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

def dashboard_summary():
    """대시보드 통계 데이터 조회"""
    conn = get_conn()
    cur = conn.cursor()
    total = cur.execute("SELECT IFNULL(SUM(qty),0) FROM inventory").fetchone()[0]
    inb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='IN' AND date(created_at)=date('now','localtime')").fetchone()[0]
    outb = cur.execute("SELECT IFNULL(SUM(qty),0) FROM history WHERE tx_type='OUT' AND date(created_at)=date('now','localtime')").fetchone()[0]
    neg = cur.execute("SELECT COUNT(*) FROM inventory WHERE qty < 0").fetchone()[0]
    conn.close()
    return {"inbound_today": inb, "outbound_today": abs(outb), "total_stock": total, "negative_stock": neg}

def rollback_inventory(tx_id: int):
    """관리자 롤백: 특정 이력을 취소하고 재고를 원상복구"""
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
