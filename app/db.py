import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 인벤토리 (6개 항목 통일: 창고, 로케이션, 품번, 품명, LOT, 규격)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse TEXT, location TEXT, item_code TEXT,
            item_name TEXT, lot_no TEXT, spec TEXT,
            qty REAL, updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 작업 로그 및 롤백용 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_type TEXT, warehouse TEXT, location TEXT,
            item_code TEXT, item_name TEXT, lot_no TEXT,
            spec TEXT, qty REAL, remark TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- 조회 함수들 ---
def get_inventory():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM inventory WHERE qty > 0").fetchall()
    conn.close()
    return [dict(i) for i in items]

def get_history():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC").fetchall()
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

# --- 작업 함수들 ---
def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark, tx_type="IN"):
    conn = get_db_connection()
    curr = conn.execute("SELECT id, qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                       (warehouse, location, item_code, lot_no)).fetchone()
    if curr:
        conn.execute("UPDATE inventory SET qty = qty + ? WHERE id = ?", (qty, curr['id']))
    else:
        conn.execute("INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) VALUES (?,?,?,?,?,?,?)",
                    (warehouse, location, item_code, item_name, lot_no, spec, qty))
    
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
                (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark))
    conn.commit()
    conn.close()

def subtract_inventory(warehouse, location, item_code, lot_no, qty, remark):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                       (warehouse, location, item_code, lot_no)).fetchone()
    if not item or item['qty'] < qty:
        conn.close()
        return False
    
    conn.execute("UPDATE inventory SET qty = qty - ? WHERE id = ?", (qty, item['id']))
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
                ("OUT", warehouse, location, item_code, item['item_name'], lot_no, item['spec'], qty, remark))
    conn.commit()
    conn.close()
    return True

def process_rollback(log_id):
    conn = get_db_connection()
    log = conn.execute("SELECT * FROM audit_logs WHERE id=?", (log_id,)).fetchone()
    if not log: return False
    
    # 반대 방향으로 재고 조정
    adj_qty = -log['qty'] if log['tx_type'] == 'IN' else log['qty']
    conn.execute("UPDATE inventory SET qty = qty + ? WHERE warehouse=? AND location=? AND item_code=? AND lot_no=?",
                (adj_qty, log['warehouse'], log['location'], log['item_code'], log['lot_no']))
    conn.execute("DELETE FROM audit_logs WHERE id=?", (log_id,))
    conn.commit()
    conn.close()
    return True
