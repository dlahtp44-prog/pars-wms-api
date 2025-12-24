import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # spec 컬럼 포함 확인
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

def get_inventory(q: str = None):
    conn = get_db_connection()
    if q:
        search = f"%{q}%"
        # 품번, 품명, LOT, 로케이션, 규격까지 검색 범위 확대
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

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    conn = get_db_connection()
    # 기존 재고 확인 시 spec도 조건에 포함하여 관리할 수 있습니다.
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
