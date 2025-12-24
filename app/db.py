import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = get_db_connection()
    # 재고 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT, location TEXT, item_code TEXT,
            item_name TEXT, lot_no TEXT, spec TEXT,
            qty REAL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 이력(로그) 테이블
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
    print("✅ 데이터베이스 및 테이블 초기화 완료")

# --- 조회 관련 함수 ---

def get_inventory(q: str = None):
    conn = get_db_connection()
    if q:
        search = f"%{q}%"
        query = "SELECT * FROM inventory WHERE qty > 0 AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR spec LIKE ? OR location LIKE ?) ORDER BY updated_at DESC"
        items = conn.execute(query, (search, search, search, search, search)).fetchall()
    else:
        items = conn.execute("SELECT * FROM inventory WHERE qty > 0 ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_history():
    """입출고 및 이동 전체 이력 조회"""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 500").fetchall()
    conn.close()
    return [dict(l) for l in logs]

def dashboard_summary():
    """대시보드 요약 데이터 계산"""
    conn = get_db_connection()
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory WHERE qty > 0").fetchone()[0] or 0
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory WHERE qty > 0").fetchone()[0] or 0
    recent_in = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE tx_type='IN' AND created_at > date('now','-1 day')").fetchone()[0] or 0
    recent_out = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE tx_type='OUT' AND created_at > date('now','-1 day')").fetchone()[0] or 0
    conn.close()
    return {
        "total_items": total_items,
        "total_qty": total_qty,
        "recent_in": recent_in,
        "recent_out": recent_out
    }

def get_location_items(location: str):
    """특정 로케이션의 재고 조회"""
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory WHERE location = ? AND qty > 0", (location,)).fetchall()
    conn.close()
    return [dict(i) for i in items]

# --- 입/출/이동 처리 함수 ---

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    conn = get_db_connection()
    curr = conn.execute("SELECT id FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?",
                       (location, item_code, lot_no, spec)).fetchone()
    if curr:
        conn.execute("UPDATE inventory SET qty = qty + ?, updated_at=DATETIME('now') WHERE id = ?", (qty, curr['id']))
    else:
        conn.execute("INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) VALUES (?,?,?,?,?,?,?)",
                    (warehouse, location, item_code, item_name, lot_no, spec, qty))
    
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
                ("IN", warehouse, location, item_code, item_name, lot_no, spec, qty, remark))
    conn.commit()
    conn.close()

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark):
    """출고 처리"""
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND qty >= ?", 
                       (location, item_code, lot_no, qty)).fetchone()
    if not item:
        conn.close()
        return False
    
    conn.execute("UPDATE inventory SET qty = qty - ?, updated_at=DATETIME('now') WHERE id = ?", (qty, item['id']))
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
                ("OUT", warehouse, location, item_code, item['item_name'], lot_no, item['spec'], qty, remark))
    conn.commit()
    conn.close()
    return True

def move_inventory(item_code, lot_no, from_loc, to_loc, qty, remark):
    """로케이션 이동 처리"""
    conn = get_db_connection()
    source = conn.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND qty >= ?", 
                         (from_loc, item_code, lot_no, qty)).fetchone()
    if not source:
        conn.close()
        return False
    
    # 기존 위치 수량 차감
    conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, source['id']))
    # 새 위치 수량 증가/생성 (warehouse는 새 로케이션 앞자리 기준 등으로 자동설정 가능하나 여기선 기존 유지)
    dest = conn.execute("SELECT id FROM inventory WHERE location=? AND item_code=? AND lot_no=?", (to_loc, item_code, lot_no)).fetchone()
    if dest:
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE id = ?", (qty, dest['id']))
    else:
        conn.execute("INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) VALUES (?,?,?,?,?,?,?)",
                    (source['warehouse'], to_loc, item_code, source['item_name'], lot_no, source['spec'], qty))
    
    conn.execute("INSERT INTO audit_logs (tx_type, item_code, item_name, lot_no, qty, from_location, to_location, remark) VALUES (?,?,?,?,?,?,?,?)",
                ("MOVE", item_code, source['item_name'], lot_no, qty, from_loc, to_loc, remark))
    conn.commit()
    conn.close()
    return True
