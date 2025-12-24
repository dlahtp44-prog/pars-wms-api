import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- 관리자 인증 및 로그 ---
def admin_password_ok(password: str) -> bool:
    """기본 비밀번호: 1234"""
    return password == "1234"

def get_admin_logs():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(l) for l in logs]

# --- 재고 조회 (검색 시 규격 포함) ---
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

# --- 입고 처리 (Spec 필수 포함) ---
def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    conn = get_db_connection()
    curr = conn.execute("SELECT id, qty FROM inventory WHERE warehouse=? AND location=? AND item_code=? AND lot_no=? AND spec=?",
                       (warehouse, location, item_code, lot_no, spec)).fetchone()
    if curr:
        conn.execute("UPDATE inventory SET qty = qty + ?, updated_at=DATETIME('now') WHERE id = ?", (qty, curr['id']))
    else:
        conn.execute("INSERT INTO inventory (warehouse, location, item_code, item_name, lot_no, spec, qty) VALUES (?,?,?,?,?,?,?)",
                    (warehouse, location, item_code, item_name, lot_no, spec, qty))
    
    conn.execute("INSERT INTO audit_logs (tx_type, warehouse, location, item_code, item_name, lot_no, spec, qty, remark) VALUES (?,?,?,?,?,?,?,?,?)",
                ("IN", warehouse, location, item_code, item_name, lot_no, spec, qty, remark))
    conn.commit()
    conn.close()
