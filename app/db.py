import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 인벤토리 테이블: 규격(spec) 컬럼 포함
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT, location TEXT, item_code TEXT,
            item_name TEXT, lot_no TEXT, spec TEXT,
            qty REAL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 이력 로그 테이블: 규격(spec) 및 이동 경로 포함
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_type TEXT, warehouse TEXT, location TEXT,
            item_code TEXT, item_name TEXT, lot_no TEXT,
            spec TEXT, qty REAL, from_location TEXT, to_location TEXT, 
            remark TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- 관리자 및 인증 관련 함수 ---

def admin_password_ok(password: str) -> bool:
    """관리자 비밀번호 일치 여부 확인 (기본: 1234)"""
    ADMIN_PW = "1234" 
    return password == ADMIN_PW

def get_admin_logs():
    """관리자용 전체 로그 조회 (최근 100건)"""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(l) for l in logs]

# --- 조회 및 대시보드 함수 ---

def dashboard_summary():
    """대시보드 요약 정보"""
    conn = get_db_connection()
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory").fetchone()[0] or 0
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory").fetchone()[0] or 0
    today_in = conn.execute("SELECT SUM(qty) FROM audit_logs WHERE tx_type='IN' AND date(created_at)=date('now')").fetchone()[0] or 0
    today_out = conn.execute("SELECT SUM(qty) FROM audit_logs WHERE tx_type='OUT' AND date(created_at)=date('now')").fetchone()[0] or 0
    conn.close()
    return {"total_qty": total_qty, "total_items": total_items, "today_in": today_in, "today_out": today_out}

def get_inventory(q: str = None):
    """재고 조회 (검색어 q가 있을 경우 규격 포함 검색)"""
    conn = get_db_connection()
    if q:
        search = f"%{q}%"
        query = """
            SELECT * FROM inventory 
            WHERE qty > 0 AND (
                item_code LIKE ? OR 
                item_name LIKE ? OR 
                lot_no LIKE ? OR 
                location LIKE ? OR 
                spec LIKE ?
            )
            ORDER BY updated_at DESC
        """
        items = conn.execute(query, (search, search, search, search, search)).fetchall()
    else:
        items = conn.execute("SELECT * FROM inventory WHERE qty > 0 ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_history(limit: int = None):
    """작업 이력 전체 조회"""
    conn = get_db_connection()
    if limit:
        logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    else:
        logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(l) for l in logs]

def get_location_items(location):
    """특정 로케이션 재고 조회"""
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory WHERE location=? AND qty > 0", (location,)).fetchall()
    conn.close()
    return [dict(i) for i in items]

# --- 재고 변동 로직 (API 연동) ---

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    """입고 처리"""
    conn = get_db_connection()
    # 창고, 로케이션, 품번, LOT, 규격이 모두 일치하는 항목 검색
    curr = conn.execute("""
        SELECT id, qty FROM inventory 
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=? AND spec=?
    """, (warehouse, location, item_code, lot_no, spec)).fetchone()
    
    if curr:
        conn.execute("UPDATE inventory SET qty = qty + ?, updated_at=DATETIME('now') WHERE id = ?", (qty, curr['id']))
    else:
        conn.execute("""
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) 
            VALUES (?,?,?,?,?,?,?)
        """, (warehouse, location, item_code, item_name, lot_no, spec, qty))
        
    conn.execute("""
        INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) 
        VALUES (?,?,?,?,?,?,?,?,?)
    """, ("IN", warehouse, location, item_code, item_name, lot_no, spec, qty, remark))
    conn.commit()
    conn.close()

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark):
    """출고 처리"""
    conn = get_db_connection()
    item = conn.execute("""
        SELECT * FROM inventory 
        WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?
    """, (warehouse, location, item_code, lot_no)).fetchone()
    
    if not item or item['qty'] < qty:
        conn.close()
        return False
        
    conn.execute("UPDATE inventory SET qty = qty - ?, updated_at=DATETIME('now') WHERE id = ?", (qty, item['id']))
    conn.execute("""
        INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) 
        VALUES (?,?,?,?,?,?,?,?,?)
    """, ("OUT", warehouse, location, item_code, item['item_name'], lot_no, item['spec'], qty, remark))
    conn.commit()
    conn.close()
    return True

def move_inventory(item_code, lot_no, from_loc, to_loc, qty, remark):
    """재고 이동 처리"""
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=?", 
                       (from_loc, item_code, lot_no)).fetchone()
    
    if not item or item['qty'] < qty:
        conn.close()
        return False
    
    # 1. 출발지 차감
    conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, item['id']))
    
    # 2. 목적지 가산 (동일 정보 재고 확인)
    dest = conn.execute("""
        SELECT id FROM inventory 
        WHERE location=? AND item_code=? AND lot_no=? AND spec=?
    """, (to_loc, item_code, lot_no, item['spec'])).fetchone()
    
    if dest:
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE id = ?", (qty, dest['id']))
    else:
        conn.execute("""
            INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) 
            VALUES (?,?,?,?,?,?,?)
        """, (item['warehouse'], to_loc, item_code, item['item_name'], lot_no, item['spec'], qty))
    
    # 3. 이동 로그 기록
    conn.execute("""
        INSERT INTO audit_logs (tx_type, warehouse, from_location, to_location, item_code, item_name, lot_no, spec, qty, remark) 
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, ("MOVE", item['warehouse'], from_loc, to_loc, item_code, item['item_name'], lot_no, item['spec'], qty, remark))
    
    conn.commit()
    conn.close()
    return True
