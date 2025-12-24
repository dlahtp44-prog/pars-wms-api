import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. 메인 재고 테이블 (6개 필수 항목 포함)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT, location TEXT, item_code TEXT,
            item_name TEXT, lot_no TEXT, spec TEXT,
            qty REAL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 2. 통합 작업 로그 (입고, 출고, 이동, 롤백 모두 기록)
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

# --- [조회 함수들] ---

def get_inventory():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory WHERE qty > 0 ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_history():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(l) for l in logs]

def dashboard_summary():
    conn = get_db_connection()
    total_qty = conn.execute("SELECT SUM(qty) FROM inventory").fetchone()[0] or 0
    total_items = conn.execute("SELECT COUNT(DISTINCT item_code) FROM inventory").fetchone()[0] or 0
    today_in = conn.execute("SELECT SUM(qty) FROM audit_logs WHERE tx_type='IN' AND date(created_at)=date('now')").fetchone()[0] or 0
    today_out = conn.execute("SELECT SUM(qty) FROM audit_logs WHERE tx_type='OUT' AND date(created_at)=date('now')").fetchone()[0] or 0
    conn.close()
    return {"total_qty": total_qty, "total_items": total_items, "today_in": today_in, "today_out": today_out}

def get_location_items(location):
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory WHERE location=? AND qty > 0", (location,)).fetchall()
    conn.close()
    return [dict(i) for i in items]

# --- [입/출고/이동 로직] ---

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    conn = get_db_connection()
    curr = conn.execute("SELECT id, qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                       (warehouse, location, item_code, lot_no)).fetchone()
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
    item = conn.execute("SELECT * FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                       (warehouse, location, item_code, lot_no)).fetchone()
    if not item or item['qty'] < qty:
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
    item = conn.execute("SELECT * FROM inventory WHERE location=? AND item_code=? AND lot_no=?", 
                       (from_loc, item_code, lot_no)).fetchone()
    if not item or item['qty'] < qty:
        conn.close()
        return False # <-- 여기서 붙어있던 에러를 수정했습니다.
    
    # 이동 대상 창고 정보 유지하며 추가
    add_inventory(item['warehouse'], to_loc, item_code, item['item_name'], lot_no, item['spec'], qty, f"이동 출처: {from_loc}")
    # 원본 위치에서 차감
    conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, item['id']))
    
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, from_location, to_location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("MOVE", item['warehouse'], from_loc, to_loc, item_code, item['item_name'], lot_no, item['spec'], qty, remark))
    conn.commit()
    conn.close()
    return True

# --- [관리자 롤백 전용] ---
def process_rollback(log_id):
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM audit_logs WHERE id=?", (log_id,)).fetchone()
    if not log: 
        conn.close()
        return False
    
    # 작업 방향의 반대로 재고 원복
    adj_qty = -log['qty'] if log['tx_type'] == 'IN' else log['qty']
    conn.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (adj_qty, log['warehouse'], log['location'], log['item_code'], log['lot_no']))
    
    # 롤백 완료 후 해당 로그 삭제
    conn.execute("DELETE FROM audit_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    return True
