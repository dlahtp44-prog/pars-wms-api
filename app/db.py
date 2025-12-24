import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT, location TEXT, item_code TEXT,
            item_name TEXT, lot_no TEXT, spec TEXT,
            qty REAL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
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

# --- 관리자 인증 관련 ---
def admin_password_ok(password: str) -> bool:
    return password == "1234"

# --- 조회 관련 함수 (에러 해결 포인트) ---

def get_history(limit: int = 500):
    """이력 조회 (limit 매개변수 추가로 TypeError 해결)"""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(l) for l in logs]

def get_inventory(q: str = None):
    conn = get_db_connection()
    if q:
        search = f"%{q}%"
        query = """
            SELECT * FROM inventory 
            WHERE qty > 0 AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR location LIKE ? OR spec LIKE ?) 
            ORDER BY updated_at DESC
        """
        items = conn.execute(query, (search, search, search, search, search)).fetchall()
    else:
        items = conn.execute("SELECT * FROM inventory WHERE qty > 0 ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(i) for i in items]

def dashboard_summary():
    conn = get_db_connection()
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory WHERE qty > 0").fetchone()[0] or 0
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory WHERE qty > 0").fetchone()[0] or 0
    recent_in = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE tx_type='IN' AND created_at > date('now','-1 day')").fetchone()[0] or 0
    recent_out = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE tx_type='OUT' AND created_at > date('now','-1 day')").fetchone()[0] or 0
    conn.close()
    return {"total_items": total_items, "total_qty": total_qty, "recent_in": recent_in, "recent_out": recent_out}

def get_location_items(location: str):
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
    conn = get_db_connection()
    source = conn.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND qty >= ?", 
                         (from_loc, item_code, lot_no, qty)).fetchone()
    if not source:
        conn.close()
        return False
    conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, source['id']))
    dest = conn.execute("SELECT id FROM inventory WHERE location=? AND item_code=? AND lot_no=? AND spec=?", 
                       (to_loc, item_code, lot_no, source['spec'])).fetchone()
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
