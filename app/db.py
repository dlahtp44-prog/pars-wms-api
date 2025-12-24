import sqlite3

def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """서버 시작 시 DB 테이블 초기화 (규격 컬럼 포함)"""
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

def get_inventory(q: str = None):
    """재고 조회 (규격 데이터 포함)"""
    conn = get_db_connection()
    if q:
        search = f"%{q}%"
        query = "SELECT * FROM inventory WHERE qty > 0 AND (item_code LIKE ? OR item_name LIKE ? OR lot_no LIKE ? OR spec LIKE ? OR location LIKE ?) ORDER BY updated_at DESC"
        items = conn.execute(query, (search, search, search, search, search)).fetchall()
    else:
        items = conn.execute("SELECT * FROM inventory WHERE qty > 0 ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(i) for i in items]

def add_inventory(warehouse, location, item_code, item_name, lot_no, spec, qty, remark):
    """입고 로직 (규격 기준으로 합산 또는 신규 생성)"""
    conn = get_db_connection()
    # 품번 + LOT + 규격이 모두 같아야 동일 재고로 취급하여 수량을 합산함
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
